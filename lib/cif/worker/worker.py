__author__ = 'James DeVincentis <james.d@hexhost.net>'

import json
import multiprocessing
import threading
import time

import pika
import setproctitle

import cif


class Thread(threading.Thread):
    def __init__(self, worker, name, backend, backendlock):
        threading.Thread.__init__(self)
        self.backend = backend
        self.backendlock = backendlock
        self.logging = cif.logging.getLogger("THREAD #{0}-{1}".format(worker, name))
        self._connection = None
        self._channel = None
        self._closing = False
        self._consumer_tag = None

    def connect(self):
        return pika.SelectConnection(parameters=pika.ConnectionParameters(host=cif.options.mq_host, port=cif.options.mq_port),
                                     on_open_callback=self.on_connection_open,
                                     on_open_error_callback=self.on_connection_open_error,
                                     stop_ioloop_on_close=False)

    def on_connection_open(self, unused_connection):
        self.add_on_connection_close_callback()
        self.open_channel()
        
    def on_connection_open_error(self, unused_connection, error_message):
        self.logging.warning("Could not connect to MQ Server. Pika Said: '{0}'".format(error_message))
    
    def add_on_connection_close_callback(self):
        self._connection.add_on_close_callback(self.on_connection_closed)

    def on_connection_closed(self, connection, reply_code, reply_text):
        self._channel = None
        if self._closing:
            self._connection.ioloop.stop()
        else:
            self.logging.warning('Connection closed, reopening in 5 seconds: (%s) %s',
                           reply_code, reply_text)
            self._connection.add_timeout(5, self.reconnect)

    def reconnect(self):
        self._connection.ioloop.stop()
        if not self._closing:
            self._connection = self.connect()
            self._connection.ioloop.start()

    def open_channel(self):
        self._connection.channel(on_open_callback=self.on_channel_open)

    def on_channel_open(self, channel):
        self._channel = channel
        self.add_on_channel_close_callback()
        self.setup_queue(cif.options.mq_work_queue_name)

    def add_on_channel_close_callback(self):
        self._channel.add_on_close_callback(self.on_channel_closed)

    def on_channel_closed(self, channel, reply_code, reply_text):
        self._connection.close()

    def setup_queue(self, queue_name):
        self._channel.queue_declare(self.on_queue_declareok, queue=queue_name, durable=True)

    def on_queue_declareok(self, method_frame):
        self._channel.basic_qos(prefetch_count=1)
        self.start_consuming()

    def start_consuming(self):
        self.add_on_cancel_callback()
        self._consumer_tag = self._channel.basic_consume(self.on_message, cif.options.mq_work_queue_name)

    def add_on_cancel_callback(self):
        self._channel.add_on_cancel_callback(self.on_consumer_cancelled)

    def on_consumer_cancelled(self, method_frame):
        if self._channel:
            self._channel.close()

    def on_message(self, unused_channel, basic_deliver, properties, body):
        self.process(body)
        self.acknowledge_message(basic_deliver.delivery_tag)

    def acknowledge_message(self, delivery_tag):
        self._channel.basic_ack(delivery_tag)

    def stop_consuming(self):
        if self._channel:
            self._channel.basic_cancel(self.on_cancelok, self._consumer_tag)

    def on_cancelok(self, unused_frame):
        self.close_channel()

    def close_channel(self):
        self._channel.close()

    def run(self):
        self._connection = self.connect()
        self._connection.ioloop.start()

    def stop(self):
        self._closing = True
        self.stop_consuming()
        self._connection.ioloop.start()

    def close_connection(self):
        self._connection.close()

    def process(self, observable):
        try:
            observable = cif.types.Observable(json.loads(observable.decode("utf-8")))
        except:
            self.logging.exception("Couldn't unserialize JSON object for processing")
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
        finally:
            # Make sure to release the lock even if we encounter but don't trap it.
            self.backendlock.release()


class Process(multiprocessing.Process):
    def __init__(self, name):
        multiprocessing.Process.__init__(self)
        self.backend = None
        self.backendlock = threading.Lock()
        self.name = name
        self.logging = cif.logging.getLogger("worker #{0}".format(name))
        self.threads = {}
        self.recycle = False
    
    def run(self):
        """Connects to the backend service, spawns and threads off into worker threads that hadnle each observable. One
        backend service connection is shared per thread however each connection *is* automatically thread safe due to
        the backend lock.

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
            for i in range(1, cif.options.worker_threads_start+1):
                if i not in self.threads or self.threads[i] is None or not self.threads[i].is_alive():
                    self.threads[i] = Thread(self.name, str(i), self.backend, self.backendlock)
                    self.threads[i].start()
            time.sleep(5)
