from .ipaddress import Ipaddress

__author__ = 'James DeVincentis <james.d@hexhost.net>'


class Ipv6(Ipaddress):
    def __init__(self, *args, **kwargs):
        self._mask = None
        super(Ipv6, self).__init__(self, args, **kwargs)

    @property
    def mask(self):
        return self._mask

    @mask.setter
    def mask(self, value):
        if self._validation and value is not None:
            if not isinstance(value, int):
                try:
                    value = int(value)
                except Exception as e:
                    raise TypeError("Mask must be an integer") from e
            if value > 128:
                raise TypeError("Mask cannot be greater than 128 bits for IPv6")
            if value < 0:
                raise TypeError("Mask cannot be less than 0 bits")
        self._mask = value
