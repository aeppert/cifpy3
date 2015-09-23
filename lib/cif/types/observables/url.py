__author__ = 'James DeVincentis <james.d@hexhost.net>'

from .address import Address


class Url(Address):
    def __init__(self, *args, **kwargs):
        super(Url, self).__init__(self, args, **kwargs)