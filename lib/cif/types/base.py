__author__ = 'James DeVincentis <james.d@hexhost.net>'

import hashlib
import os


class Base(object):
    def __init__(self):
        self._modified_fields = set()

    def _generate_random_hash(self, length=32):
        """Generate a hash from urandom data. Used largely to create unique IDs for Objects

        :param int length: Number of bytes to use when generating the hash
        :return:
        """
        tmp = hashlib.sha256()
        tmp.update(os.urandom(length))
        return tmp.hexdigest()

    def todict(self):
        """Custom todict method used for serializing objects to JSON

        :return: Dictionary of object properties
        :rtype: dict
        """
        result = {}
        for name in dir(self):
            if not callable(getattr(self, name)) and not name.startswith('_'):
                result[name] = getattr(self, name)
        return result
