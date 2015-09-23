__author__ = 'James DeVincentis <james.d@hexhost.net>'

from ..observable import Observable
from ..basics import *


class Address(Observable):
    def __init__(self, *args, **kwargs):
        # We only call the super in certain circumstances.
        if "_call_super" not in dir(self) or self._call_super:
            super(Address, self).__init__(self, args, **kwargs)
        self._portlist = None
        self._protocol = None
        self._cc = None
        self._rdata = None
        self._rtype = None

    @property
    def portlist(self):
        return self._portlist

    @portlist.setter
    def portlist(self, value):
        if value is not None:
            if isinstance(value, int):
                value = [value]
            if not isinstance(value, list):
                raise TypeError("PortList must be a list of integers")
            for v in value:
                if not isinstance(v, int):
                    raise TypeError("PortList item must be an integer")
                if v > 65535:
                    raise ValueError("PortList item cannot be greater than 65535")
                if v < 0:
                    raise ValueError("PortList item cannot be less than 0")
        self._portlist = value

    @property
    def protocol(self):
        return self._protocol
        pass

    @protocol.setter
    def protocol(self, value):
        if value is not None:
            value = protocol(value)
        self._protocol = value

    @property
    def cc(self):
        return self._cc

    @cc.setter
    def cc(self, value):
        if value is not None:
            value = country(value)
        self._cc = value

    @property
    def rdata(self):
        return self._rdata

    @rdata.setter
    def rdata(self, value):
        self._rdata = value

    @property
    def rtype(self):
        return self._rtype

    @rtype.setter
    def rtype(self, value):
        self._rtype = value
