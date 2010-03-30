from contextlib import contextmanager
from .base import TargetBase
from . import pylang
from .. import compiler


def type_to_packer(t):
    if t == compiler.t_void:
        return "None"
    if t == compiler.t_bool:
        return "packers.Bool"
    if t == compiler.t_int8:
        return "packers.Int8"
    if t == compiler.t_int16:
        return "packers.Int16"
    if t == compiler.t_int32:
        return "packers.Int32"
    if t == compiler.t_int64:
        return "packers.Int64"
    if t == compiler.t_float:
        return "packers.Float"
    if t == compiler.t_date:
        return "packers.Date"
    if t == compiler.t_buffer:
        return "packers.Buffer"
    if t == compiler.t_string:
        return "packers.Str"
    elif t == compiler.t_objref:
        return type_to_packer(compiler.t_int64) 
    if isinstance(t, (compiler.Record, compiler.Exception)):
        return "%sRecord" % (t.name,)
    if isinstance(t, compiler.Enum):
        return t.name
    if isinstance(t, compiler.Class):
        return type_to_packer(compiler.t_objref)
    return "%s$packer" % (t,)


class PythonTarget(TargetBase):
    @contextmanager
    def new_module(self, filename):
        mod = pylang.Module()
        yield mod
        with self.open(filename, "w") as f:
            f.write(mod.render())

    def generate(self, service):
        with self.new_module("%s.py" % (service.name,)) as module:
            BLOCK = module.block
            STMT = module.stmt
            SEP = module.sep
            
            STMT("import agnos")
            STMT("from agnos import packers")
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
    
            self.generate_handler_interface(module, service)
            self.generate_processor(module, service)
            self.generate_client(module, service)
    
    def generate_enum(self, module, enum):
        BLOCK = module.block
        STMT = module.stmt
        SEP = module.sep
        
        members = ["%s = %s" % (m.name, m.value) for m in enum.members]
        STMT("{0} = agnos.create_enum('{0}', {1})", enum.name, ", ".join(members))
        SEP()

    def generate_record(self, module, rec):
        BLOCK = module.block
        STMT = module.stmt
        SEP = module.sep
        
        if isinstance(rec, compiler.Exception):
            base = "agnos.PackedException"
        else:
            base = "object"
        with BLOCK("class {0}({1})", rec.name, base):
            STMT("__record_id = {0}", rec.id)
            SEP()
            args = ["%s = None" % (mem.name,) for mem in rec.members]
            with BLOCK("def __init__(self, {0})", ", ".join(args)):
                for mem in rec.members:
                    STMT("self.{0} = {0}", mem.name)
            SEP()
            with BLOCK("def pack(self, stream)"):
                STMT("agnos.packers.Int32.pack(self.__record_id, stream)")
                STMT("{0}Record.pack(self, stream)", rec.name)
        SEP()
        with BLOCK("class {0}Record(packers.Packer)", rec.name):
            STMT("@classmethod")
            with BLOCK("def pack(cls, obj, stream)"):
                for mem in rec.members:
                    STMT("{0}.pack(obj.{1}, stream)", type_to_packer(mem.type), mem.name)

            STMT("@classmethod")
            with BLOCK("def unpack(cls, stream)"):
                args = []
                for mem in rec.members:
                    args.append("%s.unpack(stream)" % (type_to_packer(mem.type),))
                STMT("return {0}({1})", rec.name, ", ".join(args))
        SEP()
    
    def generate_class_proxy(self, module, service, cls):
        BLOCK = module.block
        STMT = module.stmt
        SEP = module.sep
        DOC = module.doc
        with BLOCK("class {0}Proxy(agnos.BaseProxy)", cls.name):
            STMT("__slots__ = []")
            SEP()
            for attr in cls.attrs:
                accessors = []
                if attr.get:
                    with BLOCK("def _get_{0}(self)", attr.name):
                        STMT("return self._client._{0}_get_{1}(self._objref)", cls.name, attr.name)
                    accessors.append("_get_%s" % (attr.name,))
                if attr.set:
                    with BLOCK("def _set_{0}(self, value)", attr.name):
                        STMT("self._client._{0}_set_{1}(self._objref, value)", cls.name, attr.name)
                    accessors.append("_set_%s" % (attr.name,))
                STMT("{0} = property({1})", attr.name, ", ".join(accessors))
            SEP()
            for method in cls.methods:
                args = ", ".join(arg.name for arg in method.args)
                with BLOCK("def {0}(self, {1})", method.name, args):
                    callargs = ["self._objref"] + [arg.name for arg in method.args]
                    STMT("return _client._{0}_{1}({2})", cls.name, method.name, ", ".join(callargs))
        SEP()

    def generate_handler_interface(self, module, service):
        BLOCK = module.block
        STMT = module.stmt
        SEP = module.sep
        with BLOCK("class IHandler(object)"):
            for member in service.roots.values():
                if isinstance(member, compiler.Func):
                    args = ", ".join(arg.name for arg in member.args)
                    with BLOCK("def {0}(self, {1})", member.name, args):
                        STMT("raise NotImplementedError()")
        SEP()
    
    def generate_processor(self, module, service):
        BLOCK = module.block
        STMT = module.stmt
        SEP = module.sep
        with BLOCK("class Processor(agnos.BaseProcessor)"):
            #STMT()
            with BLOCK("def __init__(self, handler)"):
                STMT("func_mapping = {}")
                for func in service.roots.values():
                    STMT("func_mapping[{0}] = (self._func_{0}, self._unpack_{0}, self._pack_{0})", func.id)
                STMT("agnos.BaseProcessor.__init__(self, func_mapping)")
            SEP()
            for func in service.roots.values():
                if isinstance(func, compiler.Func):
                    with BLOCK("def _func_{0}(self, args)", func.id):
                        STMT("return self.handler.{0}(*args)", func.name)
                else:
                    with BLOCK("def _func_{0}(self, args)", func.id):
                        STMT("obj = args.pop(0)")
                        STMT("return obj.{0}(*args)", func.name)
                with BLOCK("def _unpack_{0}(self, stream)", func.id):
                    unpackers = []
                    for arg in func.args:
                        if isinstance(arg.type, compiler.Class):
                            unpackers.append("self.load(%s.unpack(stream))" % (type_to_packer(arg.type),))
                        else:
                            unpackers.append("%s.unpack(stream)" % (type_to_packer(arg.type),))
                    STMT("return [{0}]", ", ".join(unpackers))
                with BLOCK("def _pack_{0}(self, res, stream)", func.id):
                    if func.type == compiler.t_void:
                        STMT("pass")
                    elif isinstance(func.type, compiler.Class):
                        STMT("oid = self.store(res)")
                        STMT("{0}.pack(oid, stream)", type_to_packer(func.type))
                    else:
                        STMT("{0}.pack(res, stream)", type_to_packer(func.type))
                SEP()
        SEP()
    
    def generate_client(self, module, service):
        BLOCK = module.block
        STMT = module.stmt
        SEP = module.sep
        DOC = module.doc
        with BLOCK("class Client(agnos.BaseClient)"):
            STMT("PACKED_EXCEPTIONS = {}")
            for mem in service.types:
                if isinstance(mem, compiler.Exception):
                    STMT("PACKED_EXCEPTIONS[{0}] = {1}", mem.id, type_to_packer(mem))
            SEP()
            for func in service.roots.values():
                args = ", ".join(arg.name for arg in func.args)
                with BLOCK("def {0}(self, {1})", func.name, args):
                    STMT("_cmd_invoke({0})", func.id)
        SEP()





        









