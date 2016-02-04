import json
import multiprocessing
import setproctitle
import threading
import time

import pika

import cif

__author__ = 'James DeVincentis <james.d@hexhost.net>'


class Thread(threading.Thread):
    def __init__(self, worker, name, backend, backendlock):
        """
        Initialize the worker thread and get ready to process data

        :param worker: ID of the process this thread is under
        :type worker: str
        :param name: ID of this thread
        :type name: str
        :param backend: created and connected backend object
        :type backend: cif.backends.Backend
        :param backendlock: Lock for accessing the backend storage system
        :type backendlock: threading.Lock
        :return: None
        """
        threading.Thread.__init__(self)
        self.backend = backend
        self.backendlock = backendlock
        self.logging = cif.logging.getLogger("THREAD #{0}-{1}".format(worker, name))
        self._mq_connection = None
        self._mq_channel = None

    def run(self):
        """
        Start the worker thread

        :return:
        """
        self._mq_connection = pika.BlockingConnection(
            parameters=pika.ConnectionParameters(host=cif.options.mq_host, port=cif.options.mq_port,
                                                 retry_delay=1, socket_timeout=3, connection_attempts=5)
        )
        self._mq_channel = self._mq_connection.channel()
        self._mq_channel.queue_declare(cif.options.mq_work_queue_name, durable=True)
        self._mq_channel.exchange_declare(exchange=cif.options.mq_observable_exchange_name, type='fanout')
        self._mq_channel.basic_qos(prefetch_count=2)
        self._mq_channel.basic_consume(self.process, cif.options.mq_work_queue_name)
        try:
            self._mq_channel.start_consuming()
        except KeyboardInterrupt:
            self._mq_channel.stop_consuming()
        self._mq_channel.close()

    def process(self, channel, method_frame, header_frame, body):
        """
        Processes an incoming RabbitMQ message containing a JSON encoded observable

        :param channel: Channel the message came in on
        :type channel: pika.adapters.blocking_connection.BlockingChannel
        :param method_frame: Delivery Frame everything is inside
        :type method_frame: pika.spec.Basic.Deliver
        :param header_frame: Basic Properties Ojbect
        :type header_frame: pika.spec.BasicProperties
        :param body: RabbitMQ message to be processed
        :type body: bytearray
        :return: None
        """

        try:
            observable = cif.types.Observable(json.loads(body.decode("utf-8")))
        except:
            if not method_frame.redelivered:
                channel.basic_nack(delivery_tag=method_frame.delivery_tag)
            self.logging.exception("Couldn't processed unserialized message '{0}'".format(json.loads(body.decode("utf-8"))))
            return

        # Fetch Meta
        for name, meta in cif.worker.meta.meta.items():
            self.logging.debug("Fetching meta using: {0}".format(name))
            observable = meta(observable=observable)

        newobservables = []

        for name, plugin in cif.worker.plugins.plugins.items():
            self.logging.debug("Running plugin: {0}".format(name))
            result = plugin(observable=observable)
            if result is not None:
                for newobservable in result:
                    newobservables.append(newobservable)

        for name, meta in cif.worker.meta.meta.items():
            for key, o in enumerate(newobservables):
                self.logging.debug("Fetching meta using: {0} for new observable: {1}".format(name, key))
                newobservables[key] = meta(observable=o)

        newobservables.insert(0, observable)
        self.logging.debug("Sending {0} observables to be created.".format(len(newobservables)))
        self.backendlock.acquire()

        try:
            self.backend.observable_create(newobservables)
            channel.basic_ack(delivery_tag=method_frame.delivery_tag)
        except:
            if not method_frame.redelivered:
                channel.basic_nack(delivery_tag=method_frame.delivery_tag)
        finally:
            # Make sure to release the lock even if we encounter but don't trap it.
            self.backendlock.release()

        for observable in newobservables:
            self._mq_channel.basic_publish(cif.options.mq_observable_exchange_name, '', json.dumps(observable.todict()))

    def stop(self):
        """
        Stops the proceessing of messages

        :return:
        """
        self._mq_channel.stop_consuming()


class Process(multiprocessing.Process):
    def __init__(self, name):
        """
        Initialize a worker process and get ready to spawn threads

        :param name: ID of this worker
        :param type: str
        :return: None
        """
        multiprocessing.Process.__init__(self)
        self.backend = None
        self.backendlock = threading.Lock()
        self.name = name
        self.logging = cif.logging.getLogger("worker #{0}".format(name))
        self.threads = {}
        self._stopping = False
        self.recycle = False

    def run(self):
        """Connects to the backend service, spawns and threads off into worker threads that handle each observable. One
        backend service connection is shared per thread however each connection *is* automatically thread safe due to
        the backend lock.

        :return: None
        """
        try:
            setproctitle.setproctitle('CIF-SERVER (Worker #{0})'.format(self.name))
        except:
            pass
        self.logging.info("Starting")

        backend = __import__("cif.backends.{0:s}".format(cif.options.storage.lower()),
                             fromlist=[cif.options.storage.title()]
                             )
        self.logging.debug("Initializing Backend {0}".format(cif.options.storage.title()))

        self.backend = getattr(backend, cif.options.storage.title())()
        self.logging.debug("Connecting to Backend {0}".format(cif.options.storage_uri))

        self.backend.connect(cif.options.storage_uri)
        self.logging.debug("Connected to Backend {0}".format(cif.options.storage_uri))

        self.threads = {}

        self.logging.info("Entering worker loop")
        while True:
            if not self._stopping:
                for i in range(1, cif.options.worker_threads_start + 1):
                    if i not in self.threads or self.threads[i] is None or not self.threads[i].is_alive():
                        self.threads[i] = Thread(self.name, str(i), self.backend, self.backendlock)
                        self.threads[i].start()
            time.sleep(5)

    def stop(self):
        """
        Stop the worker process and all of it's child threads
        :return: None
        """
        self._stopping = True
        for i in range(1, cif.options.worker_threads_start + 1):
            if i in self.threads and self.threads[i] is not None and self.threads[i].is_alive():
                self.threads[i].stop()
                self.threads[i].join()