
__version__ = '0.2.1-rc.4'
__author__ = 'io.github.apluslms'
__app_id__ = 'io.github.apluslms.Roman'

import appdirs
DATA_DIR = appdirs.user_data_dir(appname=__app_id__, appauthor=__author__)
CONFIG_DIR = appdirs.user_config_dir(appname=__app_id__, appauthor=__author__)
CACHE_DIR = appdirs.user_cache_dir(appname=__app_id__, appauthor=__author__)
del appdirs

from .configuration import CourseConfig
from .builder import Builder, Engine

from . import schemas # register our schemas
