__author__ = 'James DeVincentis <james.d@hexhost.net>'

import re

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

STANDARD_TIME_FORMAT = re.compile('^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$')
