__author__ = 'James DeVincentis <james.d@hexhost.net>'

from .address import Address
from ..basics import *

class Ipaddress(Address):
    def __init__(self, *args, **kwargs):
        self._orientation = None
        self._asn = None
        self._asn_desc = None
        self._rir = None
        self._peers = []
        self._prefix = None
        self._citycode = None
        self._longitude = None
        self._latitude = None
        self._geolocation = None
        self._timezone = None
        self._subdivision = None
        self._metrocode = None
        super(Ipaddress, self).__init__(self, args, **kwargs)

    @property
    def orientation(self):
        return self._orientation

    @orientation.setter
    def orientation(self, value):
        self._orientation = value

    @property
    def asn(self):
        return self._asn

    @asn.setter
    def asn(self, value):
        self._asn = value

    @property
    def asn_desc(self):
        return self._asn_desc

    @asn_desc.setter
    def asn_desc(self, value):
        self._asn_desc = value

    @property
    def rir(self):
        return self._rir

    @rir.setter
    def rir(self, value):
        self._rir = rir(value)

    @property
    def peers(self):
        return self._peers

    @peers.setter
    def peers(self, value):
        if value is not None and not isinstance(value, list):
            raise TypeError("Peers must be a list")
        self._peers = value

    @property
    def prefix(self):
        return self._prefix

    @prefix.setter
    def prefix(self, value):
        self._prefix = value

    @property
    def citycode(self):
        return self._citycode

    @citycode.setter
    def citycode(self, value):
        if value is not None:
            value = value.upper()
        self._citycode = value

    @property
    def longitude(self):
        return self._longitude

    @longitude.setter
    def longitude(self, value):
        self._longitude = value

    @property
    def latitude(self):
        return self._latitude

    @latitude.setter
    def latitude(self, value):
        self._latitude = value

    @property
    def geolocation(self):
        return self._geolocation

    @geolocation.setter
    def geolocation(self, value):
        self._geolocation = value

    @property
    def timezone(self):
        return self._timezone

    @timezone.setter
    def timezone(self, value):
        self._timezone = value

    @property
    def subdivision(self):
        return self._subdivision

    @subdivision.setter
    def subdivision(self, value):
        self._subdivision = value