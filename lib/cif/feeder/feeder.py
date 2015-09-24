__author__ = 'James DeVincentis <james.d@hexhost.net>'

import os
import multiprocessing
import time

import cif


class Feeder(multiprocessing.Process):
    def __init__(self):
        multiprocessing.Process.__init__(self)
        self.backend = None
        self.logging = cif.logging.getLogger('FEEDER')

    def run(self):
        while True:
            self.logging.info("Starting feeder Run")
            # Based on the startup options for cif-server, let's get the backend + instantiate the class from that module
            self.logging.debug("Loading backend: {0}".format(cif.options.storage.lower()))
            backend = getattr(__import__("cif.backends.{0:s}".format(
                    cif.options.storage.lower()), fromlist=[cif.options.storage.title()]), cif.options.storage.title()
            )()

            self.logging.debug("Connecting to backend: {0}".format(cif.options.storage_uri))
            backend.connect(cif.options.storage_uri)

            self.logging.debug("Getting List of Feeds")
            files = os.listdir(cif.options.feed_directory)
            feed_files = []
            for file in files:
                if file.endswith(".yml"):
                    self.logging.debug("Found Feed File: {0}".format(file))
                    feed_files.append(os.path.join(cif.options.feed_directory, file))

            feed_files.sort()
            for feed_file in feed_files:
                self.logging.info("Loading Feed File: {0}".format(feed_file))
                feed = cif.feeder.Feed(feed_file)

                self.logging.info("Running Feed File:".format(feed_file))
                try:
                    feed.process()
                except Exception as e:
                    self.logging.exception('Exception while Running Feed {0}'.format(feed_file))

            self.logging.debug("Disconnecting from backend")
            backend.disconnect()

            self.logging.info("Sleeping feeder for {0} seconds".format(cif.options.feed_interval))
            time.sleep(cif.options.feed_interval)