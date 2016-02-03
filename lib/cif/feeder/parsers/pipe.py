from . import Delim

__author__ = 'James DeVincentis <james.d@hexhost.net>'


class Pipe(Delim):
    def __init__(self):
        super(Pipe, self).__init__()
        self.parsing_details["pattern"] = '|'
