from .address import Address

__author__ = 'James DeVincentis <james.d@hexhost.net>'


class Fqdn(Address):
    def __init__(self, *args, **kwargs):
        super(Fqdn, self).__init__(self, args, **kwargs)
