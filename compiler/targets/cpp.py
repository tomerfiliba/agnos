from contextlib import contextmanager
from .base import TargetBase
from ..langs import clike
from .. import compiler


class CPPTarget(TargetBase):
    DEFAULT_TARGET_DIR = "gen-cpp"


