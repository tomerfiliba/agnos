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
            
            DOC("templated packers")
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
                with BLOCK("return {0}", rec.name, prefix = "(", suffix = ")"):
                    for mem in rec.members:
                        STMT("{0}.unpack(stream),", type_to_packer(mem.type))
    
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
                        STMT("return self._client._autogen_{0}_get_{1}(self)", cls.name, attr.name)
                    accessors.append("_get_%s" % (attr.name,))
                if attr.set:
                    with BLOCK("def _set_{0}(self, value)", attr.name):
                        STMT("self._client._autogen_{0}_set_{1}(self, value)", cls.name, attr.name)
                    accessors.append("_set_%s" % (attr.name,))
                STMT("{0} = property({1})", attr.name, ", ".join(accessors))
            SEP()
            for method in cls.methods:
                args = ", ".join(arg.name for arg in method.args)
                with BLOCK("def {0}(self, {1})", method.name, args):
                    callargs = ["self"] + [arg.name for arg in method.args]
                    STMT("return self._client._autogen_{0}_{1}({2})", cls.name, method.name, ", ".join(callargs))

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
                with BLOCK("func_mapping = ", prefix = "{", suffix = "}"):
                    for func in service.funcs.values():
                        if func.type == compiler.t_void:
                            packer = "None"
                        else: 
                            packer = "self._pack_%s" % (func.id,)
                        STMT("{0} : (self._func_{0}, self._unpack_{0}, {1}),", func.id, packer)
                STMT("agnos.BaseProcessor.__init__(self, func_mapping, exception_map)")
            SEP()
            for func in service.funcs.values():
                self._generate_processor_function(module, func)
                self._generate_processor_unpacker(module, func)
                self._generate_processor_packer(module, func)
                SEP()
    
    def _generate_processor_function(self, module, func):
        BLOCK = module.block
        STMT = module.stmt
        SEP = module.sep
        
        if isinstance(func, compiler.Func):
            with BLOCK("def _func_{0}(self, args)", func.id):
                STMT("return self.handler.{0}(*args)", func.name)
        else:
            with BLOCK("def _func_{0}(self, args)", func.id):
                STMT("obj = args.pop(0)")
                if isinstance(func.origin, compiler.ClassAttr):
                    if func.type == compiler.t_void:
                        # setter
                        STMT("obj.{0} = args[0]", func.origin.name)
                    else:
                        # getter
                        STMT("return obj.{0}", func.origin.name)
                else:
                    STMT("return obj.{0}(*args)", func.origin.name)

    def _processor_idl_loader(self, idltype):
        if isinstance(idltype, compiler.TList):
            return "(lambda obj: [%s(item) for item in obj])" % (
                self._processor_idl_loader(idltype.oftype),)
        elif isinstance(idltype, compiler.TMap):
            return "(lambda obj: dict((%s(k), %s(v)) for k, v in obj.iteritems()))" % (
                self._processor_idl_loader(idltype.keytype),
                self._processor_idl_loader(idltype.valtype))
        elif isinstance(idltype, compiler.Class):
            return "(lambda obj: self.load(obj))"
        else:
            return "(lambda obj: obj)"

    def _generate_processor_unpacker(self, module, func):
        BLOCK = module.block
        STMT = module.stmt
        SEP = module.sep
        
        with BLOCK("def _unpack_{0}(self, stream)", func.id):
            if not func.args:
                STMT("return []")
                return 
            with BLOCK("unpacked = ", prefix = "[", suffix="]"):
                for arg in func.args:
                    if isinstance(arg.type, compiler.Class):
                        STMT("self.load({0}.unpack(stream)),", type_to_packer(arg.type))
                    elif is_complex_type(arg.type):
                        loader = self._processor_idl_loader(arg.type)
                        STMT("{0}(self.load({1}.unpack(stream))),", loader, type_to_packer(arg.type))
                    else:
                        STMT("{0}.unpack(stream),", type_to_packer(arg.type))
            STMT("return unpacked")
    
    def _processor_idl_storer(self, idltype):
        if isinstance(idltype, compiler.TList):
            return "(lambda obj: [%s(item) for item in obj])" % (
                self._processor_idl_storer(idltype.oftype),)
        elif isinstance(idltype, compiler.TMap):
            return "(lambda obj: dict((%s(k), %s(v)) for k, v in obj.iteritems()))" % (
                self._processor_idl_storer(idltype.keytype),
                self._processor_idl_storer(idltype.valtype))
        elif isinstance(idltype, compiler.Class):
            return "(lambda obj: self.store(obj))"
        else:
            return "(lambda obj: obj)"
        
    def _generate_processor_packer(self, module, func):
        BLOCK = module.block
        STMT = module.stmt
        SEP = module.sep

        if func.type == compiler.t_void:
            return 
        with BLOCK("def _pack_{0}(self, res, stream)", func.id):
            if isinstance(func.type, compiler.Class):
                STMT("{0}.pack(self.store(res), stream)", type_to_packer(func.type))
            elif is_complex_type(func.type):
                storer = self._processor_idl_storer(func.type)
                STMT("{0}.pack({1}(res), stream)", type_to_packer(func.type), storer)
            else:
                STMT("{0}.pack(res, stream)", type_to_packer(func.type))
    
    def generate_client(self, module, service):
        BLOCK = module.block
        STMT = module.stmt
        SEP = module.sep
        
        with BLOCK("class Client(agnos.BaseClient)"):
            with BLOCK("PACKED_EXCEPTIONS = ", prefix = "{", suffix = "}"):
                for mem in service.types.values():
                    if isinstance(mem, compiler.Exception):
                        STMT("{0} : {1},", mem.id, type_to_packer(mem))
            SEP()
            for func in service.funcs.values():
                args = ", ".join(arg.name for arg in func.args)
                with BLOCK("def {0}(_self, {1})", func.name, args):
                    with BLOCK("with _self._outstream.transaction()"):
                        STMT("seq = _self._invoke_command({0}, {1})", func.id, type_to_packer(func.type))
                        for arg in func.args:
                            if isinstance(arg.type, compiler.Class):
                                STMT("{0}.pack({1}._objref, _self._outstream)", type_to_packer(arg.type), arg.name)
                            else:
                                STMT("{0}.pack({1}, _self._outstream)", type_to_packer(arg.type), arg.name)
                    STMT("res = _self._get_reply(seq)")
                    if isinstance(func.type, compiler.Class):
                        STMT("return {0}Proxy(_self, res)", func.type.name)
                    elif is_complex_type(func.type):
                        loader = self._client_idl_loader(func.type)
                        STMT("return {0}(res)", loader)
                    else:
                        STMT("return res")
                SEP()
    
    def _client_idl_loader(self, idltype):
        if isinstance(idltype, compiler.TList):
            return "(lambda obj: [%s(item) for item in obj])" % (
                self._client_idl_loader(idltype.oftype),)
        elif isinstance(idltype, compiler.TMap):
            return "(lambda obj: dict((%s(k), %s(v)) for k, v in obj.iteritems()))" % (
                self._client_idl_loader(idltype.keytype),
                self._client_idl_loader(idltype.valtype))
        elif isinstance(idltype, compiler.Class):
            return "(lambda obj: %sProxy(_self, obj))" % (idltype.name,)
        elif isinstance(idltype, compiler.Record):
            loaders = [
                "%s(obj.%s)" % (self._client_idl_loader(mem.type), mem.name)
                    if is_complex_type(mem.type) else "obj.%s" % (mem.name,) 
                for mem in idltype.members]
            return "(lambda obj: %s(%s))" % (idltype.name, ", ".join(loaders))
        else:
            return "(lambda obj: obj)"
    









