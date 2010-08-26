import os
from contextlib import contextmanager


class NOOP(object):
    def __enter__(self):
        pass
    def __exit__(self, *args):
        pass
NOOP = NOOP()


class TargetBase(object):
    LANGUAGE = None
    
    def __init__(self, path):
        self.path = path
        self.mkdir("")

    def generate(self, service):
        raise NotImplementedError()

    @contextmanager
    def new_module(self, filename):
        mod = self.LANGUAGE.Module()
        yield mod
        with self.open(filename, "w") as f:
            f.write(mod.render())
    
    def mkdir(self, name):
        fullname = os.path.join(self.path, name)
        if not os.path.isdir(fullname):
            os.makedirs(fullname)
    
    def open(self, filename, mode = "w"):
        return open(os.path.join(self.path, filename), mode)



