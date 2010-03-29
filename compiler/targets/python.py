from contextlib import contextmanager
from .base import TargetBase
from . import pylang
from .. import compiler


class PythonTarget(TargetBase):
    @contextmanager
    def new_module(self, filename):
        mod = pylang.Module()
        yield mod
        with self.open(filename, "w") as f:
            f.write(mod.render())

    def generate(self, service):
        self.generate_types(service)
        self.generate_service(service)
    
    def generate_types(self, service):
        with self.new_module("types.py") as module:
            BLOCK = module.block
            STMT = module.stmt
            SEP = module.sep
            
            STMT("import agnos")
            SEP()
            for member in service.types.values():
                if isinstance(member, compiler.Enum):
                    self.generate_enum(module, member)
            
            for member in service.types.values():
                if isinstance(member, compiler.Record):
                    self.generate_record(module, member)

            for member in service.types.values():
                if isinstance(member, compiler.Class):
                    self.generate_class_proxy(module, service, member)
    
    def generate_service(self, service):
        pass












