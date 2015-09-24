__author__ = 'James DeVincentis <james.d@hexhost.net>'

from ..parser import Parser
import feedparser
import re
import io

# Regex Parser class
class Rss(Parser):
    def __init__(self):

        self.rss = feedparser.parse(self.file.read())
        self.rss_entries = len(self.rss.entries)
        self.position = 0
        self.parsing_details['values'] = []
        for element,pattern in self.parsing_details['pattern'].items():
            for value in pattern['values']:
                self.parsing_details['values'].append(value)
        self.valuecount = len(self.parsing_details['values'])

    def parsefile(self, max_objects=1000):
        """Parse file provided by self.file`. Return `max_objects` at a time. This is repetitively called

        :param int max_objects: Number of objects to return
        :return: List of parsed observables
        :rtype: list
        """

        self.loadjournal()

        observables = []

        if self.total_objects == 0 and "start" in self.parsing_details and self.parsing_details["start"] > 0:
            self.position = self.parsing_details["start"]

        objects = 0
        while objects <= max_objects:

            if self.position >= self.rss_entries:
                self.parsing = False
                break

            entry = self.rss.entries[self.position]
            self.position += 1

            results = []
            for element,pattern in self.parsing_details['pattern'].items():
                match = re.search(pattern['pattern'], entry[element])
                if match is None or match.lastindex != len(pattern["values"]):
                    self.logging.warning("No Match - element {0}; contents: '{1}'; match: {2}; values: {3}".format(
                        element, entry[element], repr(match), len(pattern["values"]))
                    )
                for index in range(1, match.lastindex+1):
                    results.append(match.group(index))


            observable = self.create_observable_from_meta_if_not_in_journal(results)
            if observable is not None:
                observables.append(observable)
                self.total_objects += 1
                objects += 1

            if self.ending and self.total_objects >= self.end:
                self.parsing = False
                break

        self.writejournal()

        return observables