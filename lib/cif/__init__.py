__author__ = 'James DeVincentis <james.d@hexhost.net>'

BINDIR = None
APPDIR = None
LIBDIR = None
ETCDIR = None
LOGDIR = None
GEODATA = None
CACHEDIR = None

MAX_BIN_SIZE = 1024 * 1024 * 10  # 10 MB

options = None
logging = None

from . import api
from . import backends
from . import feeder
from . import types
from . import worker

CONFIDENCE_MIN = 25
CONFIDENCE_DEFAULT = 75

proxies = {}
