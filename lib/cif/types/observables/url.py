from .address import Address

__author__ = 'James DeVincentis <james.d@hexhost.net>'


class Url(Address):
    def __init__(self, *args, **kwargs):
        super(Url, self).__init__(self, args, **kwargs)
