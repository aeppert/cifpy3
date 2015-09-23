__author__ = 'James DeVincentis <james.d@hexhost.net>'

from . import Delim

class Pipe(Delim):
    def __init__(self):
        super(Pipe, self).__init__()
        self.parsing_details["pattern"] = '|'
