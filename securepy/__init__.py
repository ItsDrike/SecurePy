import securepy.config.config as _conf
from securepy.restrictor import Restrictor  # noqa
from securepy.security import RESTRICTED_GLOBALS, SAFE_GLOBALS, UNRESTRICTED_GLOBALS  # noqa
from securepy.stdcapture import StdCapture  # noqa
from securepy.timing import CapturingTimedFunction, TimedFunction, TimedFunctionError  # noqa

__title__ = _conf.NAME
__author__ = _conf.AUTHOR
__licence__ = _conf.LICENCE
__copyright__ = _conf.COPYRIGHT
__version__ = _conf.VERSION
