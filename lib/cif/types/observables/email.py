__author__ = 'James DeVincentis <james.d@hexhost.net>'

import hashlib

from ..observable import Observable
from ..basics import *


class Email(Observable):
    def __init__(self, *args, **kwargs):
        # We only call the super in certain circumstances.
        if "_call_super" not in dir(self) or self._call_super:
            super(Email, self).__init__(self, args, **kwargs)
        self._hash = None
        self._htype = None

    @property
    def hash(self):
        return self._hash

    @hash.setter
    def hash(self, value):
        if value is None and self.observable is not None:
            self.htype = 'sha256'
            tmp = hashlib.sha256()
            tmp.update(self.observable)
            value = tmp.hexdigest()
        self._hash = value

    @property
    def htype(self):
        return self._htype

    @htype.setter
    def htype(self, value):
        if value is None and self.hash is not None:
            value = hash_type(value)
        self._htype = value
