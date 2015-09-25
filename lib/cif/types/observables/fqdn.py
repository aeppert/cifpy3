__author__ = 'James DeVincentis <james.d@hexhost.net>'

from .address import Address


class Fqdn(Address):
    def __init__(self, *args, **kwargs):
        super(Fqdn, self).__init__(self, args, **kwargs)
