from contextlib import contextmanager
from .base import TargetBase
from ..langs.clike import Module
from .. import compiler


class CPPTarget(TargetBase):
    DEFAULT_TARGET_DIR = "gen-cpp"


