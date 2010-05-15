import os
from .. import compiler


def is_complex_type(idltype):
    if isinstance(idltype, compiler.TList):
        return is_complex_type(idltype.oftype)
    elif isinstance(idltype, compiler.TList):
        return is_complex_type(idltype.keytype) or is_complex_type(idltype.valtype)
    elif isinstance(idltype, compiler.Class):
        return True
    elif isinstance(idltype, compiler.Record):
        return any(is_complex_type(mem.type) for mem in idltype.members)
    else:
        return False


class TargetBase(object):
    def __init__(self, path):
        self.path = path
        self.mkdir("")
    
    def generate(self, service):
        raise NotImplementedError()
    
    def mkdir(self, name):
        fullname = os.path.join(self.path, name)
        if not os.path.isdir(fullname):
            os.makedirs(fullname)
    
    def open(self, filename, mode = "w"):
        return open(os.path.join(self.path, filename), mode)



