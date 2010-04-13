from contextlib import contextmanager
from .base import TargetBase
from . import blocklang
from .. import compiler


class CPPTarget(TargetBase):
    DEFAULT_TARGET_DIR = "gen-cpp"


