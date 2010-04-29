import itertools
from contextlib import contextmanager
from .base import TargetBase
from ..langs.python import Module
from .. import compiler


def type_to_packer(t):
    if t == compiler.t_void:
        return "None"
    elif t == compiler.t_bool:
        return "packers.Bool"
    elif t == compiler.t_int8:
        return "packers.Int8"
    elif t == compiler.t_int16:
        return "packers.Int16"
    elif t == compiler.t_int32:
        return "packers.Int32"
    elif t == compiler.t_int64:
        return "packers.Int64"
    elif t == compiler.t_float:
        return "packers.Float"
    elif t == compiler.t_date:
        return "packers.Date"
    elif t == compiler.t_buffer:
        return "packers.Buffer"
    elif t == compiler.t_string:
        return "packers.Str"
    elif t == compiler.t_objref:
        return type_to_packer(compiler.t_int64) 
    elif isinstance(t, (compiler.TList, compiler.TMap)):
        return t._templated_packer
    elif isinstance(t, (compiler.Record, compiler.Exception)):
        return "%sRecord" % (t.name,)
    elif isinstance(t, compiler.Enum):
        return t.name
    elif isinstance(t, compiler.Class):
        return type_to_packer(compiler.t_objref)
    return "%r$packer" % (t,)

def const_to_python(value):
    return repr(value)

temp_counter = itertools.count(7081)

class PythonTarget(TargetBase):
    DEFAULT_TARGET_DIR = "."

    @contextmanager
    def new_module(self, filename):
        mod = Module()
        yield mod
        with self.open(filename, "w") as f:
            f.write(mod.render())

    def generate(self, service):
        with self.new_module("%s_bindings.py" % (service.name,)) as module:
            BLOCK = module.block
            STMT = module.stmt
            SEP = module.sep
            DOC = module.doc
            
            STMT("import agnos")
            STMT("from agnos import packers")
            SEP()
            
            STMT("_IDL_MAGIC = '{0}'", service.digest)
            SEP()

            DOC("templated packers", spacer = True)
            self.generate_templated_packer(module, service)
            SEP()
            
            DOC("enums", spacer = True)
            for member in service.types.values():
                if isinstance(member, compiler.Enum):
                    self.generate_enum(module, member)
                    SEP()
            
            DOC("records", spacer = True)
            for member in service.types.values():
                if isinstance(member, compiler.Record):
                    self.generate_record(module, member)
                    SEP()
            
            DOC("consts", spacer = True)
            for member in service.consts.values():
                STMT("{0} = {1}", member.name, const_to_python(member.value))
            SEP()
            
            DOC("classes", spacer = True)
            for member in service.types.values():
                if isinstance(member, compiler.Class):
                    self.generate_class_proxy(module, service, member)
                    SEP()
            SEP()
            
            DOC("server", spacer = True)
            self.generate_handler_interface(module, service)
            SEP()
            
            self.generate_processor(module, service)
            SEP()
            
            DOC("client", spacer = True)
            self.generate_client(module, service)
            SEP()

    def _generate_templated_packer_for_type(self, tp):
        if isinstance(tp, compiler.TList):
            return "packers.ListOf(%s)" % (self._generate_templated_packer_for_type(tp.oftype),)
        elif isinstance(tp, compiler.TList):
            return "packers.MapOf(%s, %s)" % (self._generate_templated_packer_for_type(tp.keytype),
                self._generate_templated_packer_for_type(tp.valtype))
        else:
            return type_to_packer(tp)

    def generate_templated_packer(self, module, service):
        BLOCK = module.block
        STMT = module.stmt
        SEP = module.sep
        
        mapping = {}
        for tp in service.all_types:
            if isinstance(tp, (compiler.TList, compiler.TMap)):
                definition = self._generate_templated_packer_for_type(tp)
                if definition in mapping:
                    tp._templated_packer = mapping[definition]
                else:
                    tp._templated_packer = "_templated_packer_%s" % (temp_counter.next(),)
                    STMT("{0} = {1}", tp._templated_packer, definition)
                    mapping[definition] = tp._templated_packer
    
    def generate_enum(self, module, enum):
        BLOCK = module.block
        STMT = module.stmt
        SEP = module.sep
        
        members = ["\n    '%s' : %s" % (m.name, m.value) for m in enum.members]
        STMT("{0} = agnos.create_enum('{0}', {{{1}}})", enum.name, ", ".join(members))

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
            with BLOCK("def __repr__(self)"):
                attrs = ["self.%s" % (mem.name,) for mem in rec.members]
                STMT("attrs = [{0}]", ", ".join(attrs))
                STMT("return '{0}(%s)' % (', '.join(repr(a) for a in attrs),)", rec.name)
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
                        STMT("return self._client._{0}_get_{1}(self)", cls.name, attr.name)
                    accessors.append("_get_%s" % (attr.name,))
                if attr.set:
                    with BLOCK("def _set_{0}(self, value)", attr.name):
                        STMT("self._client._{0}_set_{1}(self, value)", cls.name, attr.name)
                    accessors.append("_set_%s" % (attr.name,))
                STMT("{0} = property({1})", attr.name, ", ".join(accessors))
            SEP()
            for method in cls.methods:
                args = ", ".join(arg.name for arg in method.args)
                with BLOCK("def {0}(self, {1})", method.name, args):
                    callargs = ["self"] + [arg.name for arg in method.args]
                    STMT("return self._client._{0}_{1}({2})", cls.name, method.name, ", ".join(callargs))

    def generate_handler_interface(self, module, service):
        BLOCK = module.block
        STMT = module.stmt
        SEP = module.sep
        with BLOCK("class IHandler(object)"):
            for member in service.funcs.values():
                if isinstance(member, compiler.Func):
                    args = ", ".join(arg.name for arg in member.args)
                    with BLOCK("def {0}(self, {1})", member.name, args):
                        STMT("raise NotImplementedError()")
    
    def generate_processor(self, module, service):
        BLOCK = module.block
        STMT = module.stmt
        SEP = module.sep
        with BLOCK("class Processor(agnos.BaseProcessor)"):
            with BLOCK("def __init__(self, handler, exception_map = {})"):
                STMT("self.handler = handler")
                STMT("func_mapping = {}")
                for func in service.funcs.values():
                    if func.type == compiler.t_void:
                        packer = "None"
                    else: 
                        packer = "self._pack_%s" % (func.id,)
                    STMT("func_mapping[{0}] = (self._func_{0}, self._unpack_{0}, {1})", func.id, packer)
                STMT("agnos.BaseProcessor.__init__(self, func_mapping, exception_map)")
            SEP()
            for func in service.funcs.values():
                if isinstance(func, compiler.Func):
                    with BLOCK("def _func_{0}(self, args)", func.id):
                        STMT("return self.handler.{0}(*args)", func.name)
                else:
                    with BLOCK("def _func_{0}(self, args)", func.id):
                        STMT("obj = args.pop(0)")
                        STMT("return obj.{0}(*args)", func.origin.name)
                with BLOCK("def _unpack_{0}(self, stream)", func.id):
                    unpackers = []
                    for arg in func.args:
                        if isinstance(arg.type, compiler.Class):
                            unpackers.append("self.load(%s.unpack(stream))" % (type_to_packer(arg.type),))
                        else:
                            unpackers.append("%s.unpack(stream)" % (type_to_packer(arg.type),))
                    STMT("return [{0}]", ", ".join(unpackers))
                if func.type != compiler.t_void:
                    with BLOCK("def _pack_{0}(self, res, stream)", func.id):
                        if isinstance(func.type, compiler.Class):
                            STMT("oid = self.store(res)")
                            STMT("{0}.pack(oid, stream)", type_to_packer(func.type))
                        else:
                            STMT("{0}.pack(res, stream)", type_to_packer(func.type))
                SEP()
    
    def generate_client(self, module, service):
        BLOCK = module.block
        STMT = module.stmt
        SEP = module.sep
        DOC = module.doc
        with BLOCK("class Client(agnos.BaseClient)"):
            STMT("PACKED_EXCEPTIONS = {}")
            for mem in service.types.values():
                if isinstance(mem, compiler.Exception):
                    STMT("PACKED_EXCEPTIONS[{0}] = {1}", mem.id, type_to_packer(mem))
            SEP()
            for func in service.funcs.values():
                args = ", ".join(arg.name for arg in func.args)
                with BLOCK("def {0}(self, {1})", func.name, args):
                    with BLOCK("with self._outstream.transaction()"):
                        STMT("self._cmd_invoke({0})", func.id)
                        for arg in func.args:
                            if isinstance(arg.type, compiler.Class):
                                STMT("{0}.pack({1}._objref, self._outstream)", type_to_packer(arg.type), arg.name)
                            else:
                                STMT("{0}.pack({1}, self._outstream)", type_to_packer(arg.type), arg.name)
                    STMT("seq, res = self._read_reply({0})", type_to_packer(func.type))
                    if isinstance(func.type, compiler.Class):
                        STMT("return {0}Proxy(self, res)", func.type.name)
                    elif func.type != compiler.t_void:
                        STMT("return res")





        









