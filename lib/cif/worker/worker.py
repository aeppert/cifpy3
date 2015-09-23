__author__ = 'James DeVincentis <james.d@hexhost.net>'

import multiprocessing
import threading
import queue
import time

import cif

tasks = multiprocessing.Queue(131072)

class Thread(threading.Thread):
    def __init__(self, worker, name, queue, backend, backendlock):
        threading.Thread.__init__(self)
        self.backend = backend
        self.backendlock = backendlock
        self.queue = queue
        self.logging = cif.logging.getLogger("THREAD #{0}-{1}".format(worker, name))

    def run(self):
        self.logging.debug("Booted")
        # Loop forever
        while True:
            # Wait for a task
            observable = self.queue.get()
            if observable is None:
                break
            self.logging.debug("Thread Loop: Got observable")
            # Run meta augmentation on the first observable
            for name,meta in cif.worker.meta.meta.items():
                self.logging.debug("Fetching meta using: {0}".format(name))
                observable = meta(observable=observable)
            # Add observable to list
            newobservables = []
            # Run all plugins first
            # plugins may create additional observables
            for name,plugin in cif.worker.plugins.plugins.items():
                self.logging.debug("Running plugin: {0}".format(name))
                result = plugin(observable=observable)
                if result is not None:
                    for newobservable in result:
                        newobservables.append(newobservable)

            # Then run the meta augmentation on the observables we now have.
            for name,meta in cif.worker.meta.meta.items():
                for key, o in enumerate(newobservables):
                    self.logging.debug("Fetching meta using: {0} for new observable: {1}".format(name, key))
                    newobservables[key] = meta(observable=o)

            # Add all of the observables back to the backend
            # Including our original
            newobservables.insert(0, observable)
            self.logging.debug("Sending {0} observables to be created.".format(len(newobservables)))
            self.backendlock.acquire()
            try:
                self.backend.observable_create(observable=newobservables)
            finally:
                self.backendlock.release()
            self.logging.debug("worker Loop: End")



# This thread will simply move items from our multiprocess queue to our threaded queue
class QueueManager(threading.Thread):
    def __init__(self, worker, source, destination):
        threading.Thread.__init__(self)
        self.source = source
        self.destination = destination
        self.die = False

    def run(self):
        while True:
            observable = self.source.get()
            if observable is None:
                for i in range(1, cif.options.threads+1):
                    self.destination.put(None)
                self.die = True
                break
            else:
                self.destination.put(observable)


class Process(multiprocessing.Process):
    def __init__(self, name):
        multiprocessing.Process.__init__(self)
        self.backend = None
        self.backendlock = threading.Lock()
        self.name = name
        self.logging = cif.logging.getLogger("worker #{0}".format(name))
        self.queue = queue.Queue(cif.options.threads*2)
        self.threads = {}

    def run(self):

        # Initialize backend
        self.logging.info("Starting")

        # Based on the startup options for cif-server, let's get the backend
        backend = __import__("cif.backends.{0:s}".format(cif.options.storage.title()),
                             fromlist=[cif.options.storage.title()]
                             )
        self.logging.debug("Initializing Backend {0}".format(cif.options.storage.title()))

        # Now instantiate the class from that module
        self.backend = getattr(backend, cif.options.storage.title())()
        self.logging.debug("Connecting to Backend {0}".format(cif.options.storage_uri))

        # Connect to the backend
        self.backend.connect(cif.options.storage_uri)
        self.logging.debug("Connected to Backend {0}".format(cif.options.storage_uri))

        # Boot up queue manager
        self.logging.debug("Booting worker #{0} Queue Manager".format(self.name))

        # Allocate for out threads
        self.threads = {}

        # Allocate the queue manager
        queuemanager = None

        self.logging.info("Entering worker loop")
        while True:
            # Check to see if the queue manager is running
            if queuemanager is None or not queuemanager.is_alive():
                # Our poisoned pill will come from the queue manager
                if queuemanager is not None and queuemanager.die:
                    # Break out
                    break
                # If we aren't poisoned restart the queue manager
                queuemanager = QueueManager(self.name, tasks, self.queue)
                queuemanager.start()

            # Check to see if all of the threads are running
            for i in range(1, cif.options.threads+1):
                if i not in self.threads or self.threads[i] is None or not self.threads[i].is_alive():
                    self.threads[i] = Thread(self.name, str(i), self.queue, self.backend, self.backendlock)
                    self.threads[i].start()

            # Enter the sleep loop
            time.sleep(5)
