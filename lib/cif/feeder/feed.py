import os
import json
import datetime
import gzip
import tempfile
import zipfile
import multiprocessing

import pika
import requests

import cif
from .parser import Parser

__author__ = 'James DeVincentis <james.d@hexhost.net>'


class Feed(multiprocessing.Process):
    def __init__(self, feed_config, feed_name):
        multiprocessing.Process.__init__(self)
        self.feed_name = feed_name
        self.feed_config = feed_config
        self.logging = cif.logging.getLogger('FEED')
        self.logging.info("Setting up RabbitMQ Queues")
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(host=cif.options.mq_host, port=cif.options.mq_port))
        self.channel = self.connection.channel()
        self.channel.queue_declare(queue=cif.options.mq_work_queue_name, durable=True)
    def run(self):
        """Retrieves the feed, passes it to a parser, and then passes parsed observables to the workers

        :return:
        """
        if "feeds" not in self.feed_config.keys():
            return
        if self.feed_name not in self.feed_config['feeds']:
            return
        
        # These are fields that are used for control when parsing and should not be passed down to the observables
        fields_to_strip = ['node', 'map', 'values', 'pattern', 'remote', 'parser',
                           'username', 'password', 'method', 'start', 'end', 'interval']

        # Pull out parsing details for feeds from defined meta
        feed_parsing_details = dict((name, self.feed_config["feeds"][self.feed_name][name]) for name in fields_to_strip if name in self.feed_config["feeds"][self.feed_name].keys())
        feed_parsing_details['feed_name'] = self.feed_name

        # Exclude control fields from defined meta for created observables
        feed_meta = dict((name, self.feed_config["feeds"][self.feed_name][name]) for name in self.feed_config["feeds"][self.feed_name].keys() if name not in fields_to_strip)

        if "method" not in feed_parsing_details.keys():
            feed_parsing_details["method"] = "GET"

        if "parser" not in feed_parsing_details.keys():
            feed_parsing_details["parser"] = "regex"

        if "values" not in feed_parsing_details.keys():
            feed_parsing_details["values"] = ["observable"]
        elif not isinstance(feed_parsing_details["values"], list):
            feed_parsing_details["values"] = [feed_parsing_details["values"]]

        feed_parsing_details["journal"] = "{0}/{1}-{2}-{3}-journal.pickle".format(
            cif.CACHEDIR, os.path.basename(self.feed_config['filename'].lower()), self.feed_name.lower(),
            datetime.datetime.utcnow().strftime("%Y-%m-%d")
        )
        self.logging.debug("Built Journal Path: {0}".format(feed_parsing_details['journal']))

        if feed_parsing_details["remote"].startswith('/'):
            self.logging.debug("Local file detected '{0}'. Opening Locally.".format(feed_parsing_details["remote"]))
            temp = open(feed_parsing_details["remote"], "rb")
        else:
            self.logging.debug("Remote file detected '{0}'. Opening remotely.".format(
                feed_parsing_details["remote"])
            )
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/45.0.2454.93 Safari/537.36'
            }
            try:
                response = requests.request(feed_parsing_details["method"], feed_parsing_details["remote"],
                                            proxies=cif.proxies, stream=True, headers=headers, verify=False, timeout=300
                                            )
            except:
                self.logging.exception("Could not fetch remote url '{0}'".format(feed_parsing_details["remote"]))
                return

            if response.status_code > 300:
                self.logging.error("Failed fetching remote feed '{0}': {1} {2}".format(
                    feed_parsing_details["remote"], response.status_code, response.reason)
                )
                return

            temp = tempfile.TemporaryFile(mode="w+b")

            for chunk in response.iter_content(1024 * 1024):
                temp.write(chunk)

            response.close()

            self.logging.debug("Wrote {0} bytes to binary file.".format(temp.tell()))

            temp.seek(0)

        zip_file = None
        if zipfile.is_zipfile(temp):
            zip_file = zipfile.ZipFile(temp)
            temp_bin = zip_file.open(zip_file.namelist()[0])
        else:
            temp_bin = temp
            temp_bin.seek(0)

        if zip_file is None:
            test_header = temp.read(2)
            temp.seek(0)
            if test_header == b'\x1f\x8b':
                temp_bin = gzip.open(temp)
            else:
                temp_bin = temp

        file_to_parse = tempfile.TemporaryFile(mode="w+", encoding="ISO8859-1")
        while True:
            buf = temp_bin.read(1024 * 1024)
            if len(buf) == 0:
                break
            file_to_parse.write(buf.decode("ISO8859-1"))
        self.logging.debug("Wrote {0} bytes to text file.".format(file_to_parse.tell()))
        file_to_parse.seek(0)

        if zip_file is not None:
            zip_file.close()
        temp_bin.close()

        self.logging.debug("Creating Parser for feed {0}".format(feed_parsing_details['remote']))
        parser = Parser(parsing_details=feed_parsing_details, basemeta=feed_meta, file=file_to_parse)

        while parser.parsing:
            observables = parser.parsefile(2000)
            if len(observables) > 0:
                self.logging.debug("Feed '{0}' is sending {1} new objects to be processed".format(
                    feed_parsing_details['remote'], len(observables))
                )
                for observable in observables:
                    self.channel.basic_publish(
                        exchange='',
                        routing_key=cif.options.mq_work_queue_name,
                        body=json.dumps(observable.todict()),
                        properties=pika.BasicProperties(
                                delivery_mode = 2, # make message persistent
                        )
                    )

        file_to_parse.close()
        self.connection.close()
        self.logging.debug("Finished Parsing feed {0}".format(feed_parsing_details['remote']))
