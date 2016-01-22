__author__ = 'James DeVincentis <james.d@hexhost.net>'

import multiprocessing
import threading
import time
import queue

import setproctitle

import cif

tasks = multiprocessing.Queue(262144)


class Thread(threading.Thread):
    def __init__(self, worker, name, q, backend, backendlock):
        threading.Thread.__init__(self)
        self.backend = backend
        self.backendlock = backendlock
        self.queue = q
        self.logging = cif.logging.getLogger("THREAD #{0}-{1}".format(worker, name))

    def run(self):
        """Runs in infinite loop waiting for items from this worker's queue. Each worker has 'cif.options.threads' of
        these running at any one given time.

        """
        self.logging.debug("Booted")
        while True:
            observable = self.queue.get()
            if observable is None:
                self.logging.debug("Thread got pill. Shutting down.")
                break
            self.logging.debug("Got {0} from local queue: {1}".format(repr(observable), observable.observable))
            self.logging.debug("Thread Loop: Got observable")

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

            self.logging.debug("worker Loop: End")


class QueueManager(threading.Thread):
    def __init__(self, worker, source, destination):
        threading.Thread.__init__(self)
        self.source = source
        self.destination = destination
        self.worker = worker
        self.die = False
        self.logging = cif.logging.getLogger("Manager #{0}".format(worker))
        self.cycles_remaining = 10000000

    def run(self):
        """Runs in an infinite loop taking any tasks from the main queue and distributing it to the workers. First one
        to grab it from the main queue wins. Each worker process has one of these threads.

        """
        while True:
            self.logging.debug("Waiting for item from global queue: {0}".format(repr(self.source)))
            observable = self.source.get()
            if observable is None:
                self.kill_children()
                break
            else:
                self.logging.debug("Got {0} from global queue: {1}".format(repr(observable), observable.observable))
                self.logging.debug("Put {0} into local queue: {1}".format(repr(observable), observable.observable))
                self.destination.put(observable)
                self.cycles_remaining -= 1
                if self.cycles_remaining < 1:
                    self.logging.debuging("Triggering Recycle")
                    self.kill_children()
                    break
                
    def kill_children(self):
        self.logging.debug("Manager Got pill. Passing to threads.")
        for i in range(1, cif.options.threads+1):
            self.logging.debug("Distributed pill to Thread #{0}".format(i))
            self.destination.put(None)
        self.die = True


class Process(multiprocessing.Process):
    def __init__(self, name):
        multiprocessing.Process.__init__(self)
        self.backend = None
        self.backendlock = threading.Lock()
        self.name = name
        self.logging = cif.logging.getLogger("worker #{0}".format(name))
        self.queue = multiprocessing.Queue(cif.options.threads*2)
        self.threads = {}
        self.recycle = False
    
    def run(self):
        """Connects to the backend service, spawns and threads off into worker threads that hadnle each observable. One
        backend service connection is shared per thread however each connection *is* automatically thread safe due to
        the backend lock.

        """
        try:
            setproctitle.setproctitle('[CIF-SERVER] - Worker #{0}'.format(self.name))
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
        queuemanager = None

        self.logging.info("Entering worker loop")
        while True:
            if queuemanager is None or not queuemanager.is_alive():
                # Check to see if the queue manager got a poison pill. We don't manage the queue directly so we trust
                #   the queue manager to see if it got one.
                if queuemanager is not None and self.cycles_remaining < 1:
                    self.recycle = True
                    for i in range(1, cif.options.threads+1):
                        if i in self.threads and self.threads[i] is not None:
                            self.threads[i].join()
                    break
                if queuemanager is not None and queuemanager.die:
                    break
                queuemanager = QueueManager(self.name, tasks, self.queue)
                queuemanager.start()
            self.logging.debug("Local Queue Size: {0}".format(self.queue.qsize()))
        
            for i in range(1, cif.options.threads+1):
                if i not in self.threads or self.threads[i] is None or not self.threads[i].is_alive():
                    self.threads[i] = Thread(self.name, str(i), self.queue, self.backend, self.backendlock)
                    self.threads[i].start()
                
            
            time.sleep(5)
