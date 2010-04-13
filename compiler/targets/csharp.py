from contextlib import contextmanager
from .base import TargetBase
from . import blocklang
from .. import compiler


class CSharpTarget(TargetBase):
    DEFAULT_TARGET_DIR = "gen-csharp"


