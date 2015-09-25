__author__ = 'James DeVincentis <james.d@hexhost.net>'

import socket

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
            if not isinstance(value, list):
                if isinstance(value, str):
                    try:
                        ports = value.split(',')
                        value = []
                        for port in ports:
                            start_and_end = port.split('-')
                            if len(start_and_end) == 2:
                                for i in range(int(start_and_end[0]), int(start_and_end[1])+1):
                                    value.append(i)
                            else:
                                value.append(int(port))
                    except Exception as e:
                        raise TypeError("Could not parse portlist") from e
                if isinstance(value, int):
                    try:
                        value = [int(value)]
                    except Exception as e:
                        raise TypeError("PortList must be a list of integers") from e

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

    @property
    def application(self):
        return self._application

    @application.setter
    def application(self, value):
        if value is not None and self.portlist is None:
            # noinspection PyBroadException
            try:
                self.portlist = [socket.getservbyname(value)]
            except:
                pass
        self._application = value
