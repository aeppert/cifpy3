import multiprocessing
import os
import setproctitle
import time
import watchdog.observers
import yaml

import schedule

import cif

__author__ = 'James DeVincentis <james.d@hexhost.net>'


class Feeder(multiprocessing.Process):
    def __init__(self):
        # Initialize basics
        multiprocessing.Process.__init__(self)
        self.logging = cif.logging.getLogger('FEEDER')
        self._reload = True

        # Create our watchdog to signal for reloading Feeds
        self.watchdog = watchdog.observers.Observer()
        self.watchdog.schedule(self._signal_reload, cif.options.feed_directory, recursive=True)
        self.watchdog.start()

    def _signal_reload(self, event):
        self.logging.debug("Got {0} event for '{1}'.".format(event.event_type, event.src_path))

        # Don't do anything for directory changes
        if event.is_directory:
            return

        # Don't do anything unless it ends in .yml
        if not event.src_path.ends('.yml'):
            return

        # Don't do anything if it starts with a .
        if os.path.basename(event.src_path).startswith('.'):
            return

        self.logging.debug("Signaling reload due to {0} event for '{1}'.".format(event.event_type, event.src_path))
        self._reload = True

    def _do_reload(self):
        schedule.clear()
        self.feeds = {}
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

            self.feeds[feed_file] = self._load_feed(feed_file)

            self.logging.info("Scheduling Feed File:".format(feed_file))

            if 'feeds' not in self.feeds[feed_file]:
                continue

            for feed_name in self.feeds[feed_file]['feeds'].keys():

                if "interval" in self.feeds[feed_file]['feeds'][feed_name]:
                    if self.feeds[feed_file]['feeds'][feed_name]['interval'] == "hourly":

                        self.logging.debug(
                                repr(schedule.every().hour.at("00:00").do(self._run_feed, feed_file, feed_name))
                        )

                    elif self.feeds[feed_file]['feeds'][feed_name]['interval'] == "daily":

                        self.logging.debug(
                                repr(schedule.every().day.at("00:00").do(self._run_feed, feed_file, feed_name))
                        )

                    elif self.feeds[feed_file]['feeds'][feed_name]['interval'] == "weekly":

                        self.logging.debug(
                                repr(schedule.every().week.at("00:00").do(self._run_feed, feed_file, feed_name))
                        )

                    else:

                        self.logging.debug(
                                repr(schedule.every().hour.at("00:00").do(self._run_feed, feed_file, feed_name))
                        )
                else:
                    self.logging.debug(
                            repr(schedule.every().hour.at("00:00").do(self._run_feed, feed_file, feed_name))
                    )

    def _run_feed(self, feed_file, feed_name):
        process = cif.feeder.Feed(feed_config=self.feeds[feed_file], feed_name=feed_name)
        process.run()
        process.join()

    def _load_feed(self, feed_file):
        try:
            self.logging.debug("Opening Feed file for parsing")
            with open(feed_file, 'r') as stream:
                self.logging.debug("Parsing feed file")
                feed_config = yaml.load(stream)
        except IOError as e:
            self.logging.exception("Could not parse feed file {0}: {1}".format(feed_file), e)
            return

        if "feeds" not in feed_config.keys():
            self.logging.info("No feeds configured inside of {0}. Moving on to next file.".format(feed_file))
            return

        if "parser" in feed_config.keys():
            for key, value in feed_config["feeds"].items():
                if "parser" not in feed_config["feeds"][key].keys():
                    feed_config["feeds"][key]["parser"] = feed_config["parser"]

        if "defaults" in feed_config.keys():
            for key, value in feed_config["defaults"].items():
                for k, v in feed_config["feeds"].items():
                    if key not in feed_config["feeds"][k].keys():
                        feed_config["feeds"][k][key] = value

        feed_config['filename'] = feed_file

        return feed_config

    def run(self):
        # Set our process title, we don't care if it fails
        try:
            setproctitle.setproctitle('[CIF-SERVER] - Feeder')
        except:
            pass

        # Enter a loop for scheduled events / detecting changes
        while True:
            schedule.run_pending()
            if self._reload:
                self._do_reload()
                self._reload = False

            time.sleep(1)
