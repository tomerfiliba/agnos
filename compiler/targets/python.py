import itertools
from contextlib import contextmanager
from .base import TargetBase, is_complex_type
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
    elif isinstance(t, (compiler.TList, compiler.TMap)):
        return "_%s" % (t.stringify(),)
    elif isinstance(t, (compiler.Enum, compiler.Record, compiler.Exception)):
        return "%sPacker" % (t.name,)
    elif isinstance(t, compiler.Class):
        return "%sObjRef" % (t.name,)
    return "%r$$$packer" % (t,)

def const_to_python(typ, val):
    if val is None:
        return "None"
    elif typ == compiler.t_bool:
        if val:
            return "True"
        else:
            return "False"
    elif typ == compiler.t_int8:
        return repr(val)
    elif typ == compiler.t_int16:
        return repr(val)
    elif typ == compiler.t_int32:
        return repr(val)
    elif typ == compiler.t_int64:
        return repr(val)
    elif typ == compiler.t_float:
        return repr(val)
    elif typ == compiler.t_string:
        return repr(val)
    elif isinstance(typ, compiler.TList):
        return "[%s]" % (", ".join(const_to_cs(typ.oftype, item) for item in val),)
    else:
        raise IDLError("%r cannot be converted to a c# const" % (val,))


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
            STMT("from agnos import utils")
            SEP()
            
            STMT("AGNOS_VERSION = 'Agnos 1.0'")
            STMT("IDL_MAGIC = '{0}'", service.digest)
            SEP()
            
            DOC("enums", spacer = True)
            for member in service.types.values():
                if isinstance(member, compiler.Enum):
                    self.generate_enum(module, member)
                    SEP()
            
            DOC("records", spacer = True)
            for member in service.types.values():
                if isinstance(member, compiler.Record):
                    self.generate_record_class(module, member)
                    SEP()
            
            for member in service.types.values():
                if isinstance(member, compiler.Record):
                    if not is_complex_type(member):
                        self.generate_record_packer(module, member)
                        SEP()
            
            DOC("consts", spacer = True)
            for member in service.consts.values():
                STMT("{0} = {1}", member.name, const_to_python(member.type, member.value))
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
        elif isinstance(tp, compiler.TMap):
            return "packers.MapOf(%s, %s)" % (self._generate_templated_packer_for_type(tp.keytype),
                self._generate_templated_packer_for_type(tp.valtype))
        else:
            return type_to_packer(tp)

    def generate_templated_packers(self, module, service):
        BLOCK = module.block
        STMT = module.stmt
        SEP = module.sep
        
        for tp in service.all_types:
            if isinstance(tp, (compiler.TList, compiler.TMap)):
                definition = self._generate_templated_packer_for_type(tp)
                STMT("_{0} = {1}", tp.stringify(), definition)

    def generate_enum(self, module, enum):
        BLOCK = module.block
        STMT = module.stmt
        SEP = module.sep
        
        members = ["\n    '%s' : %s" % (m.name, m.value) for m in enum.members]
        STMT("{0} = utils.create_enum('{0}', {{{1}}})", enum.name, ", ".join(members))
        SEP()
        with BLOCK("class {0}Packer(packers.Packer)", enum.name):
            STMT("@classmethod")
            with BLOCK("def pack(cls, obj, stream)"):
                STMT("packers.Int32.pack(obj.value, stream)")
            STMT("@classmethod")
            with BLOCK("def unpack(cls, stream)"):
                STMT("{0}.get_by_value(packers.Int32.unpack(stream))", enum.name)

    def generate_record_class(self, module, rec):
        BLOCK = module.block
        STMT = module.stmt
        SEP = module.sep
        
        if isinstance(rec, compiler.Exception):
            base = "agnos.PackedException"
        else:
            base = "object"
        with BLOCK("class {0}({1})", rec.name, base):
            STMT("_recid = {0}", rec.id)
            STMT("_ATTRS = [{0}]", ", ".join(repr(mem.name) for mem in rec.members))
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

    def generate_record_packer(self, module, rec):
        BLOCK = module.block
        STMT = module.stmt
        SEP = module.sep
        
        with BLOCK("class {0}Packer(packers.Packer)", rec.name):
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
            if cls.attrs:
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
            STMT("__slots__ = []")
            for member in service.funcs.values():
                if isinstance(member, compiler.Func):
                    args = ", ".join(arg.name for arg in member.args)
                    with BLOCK("def {0}(self, {1})", member.fullname, args):
                        STMT("raise NotImplementedError()")

    def generate_processor(self, module, service):
        BLOCK = module.block
        STMT = module.stmt
        SEP = module.sep
        with BLOCK("def Processor(handler, exception_map = {})"):
            for func in service.funcs.values():
                self._generate_processor_function(module, func)
                self._generate_processor_unpacker(module, func)
            SEP()
            STMT("proc = agnos.BaseProcessor()")
            STMT("storer = proc.store")
            STMT("loader = proc.load")
            SEP()
            for tp in service.types.values():
                if isinstance(tp, compiler.Class):
                    STMT("{0}ObjRef = packers.ObjRef(storer, loader)", tp.name)
            SEP()
            for member in service.types.values():
                if isinstance(member, compiler.Record):
                    if is_complex_type(member):
                        self.generate_record_packer(module, member)
                        SEP()
            self.generate_templated_packers(module, service)
            SEP()
            with BLOCK("func_mapping = ", prefix = "{", suffix = "}"):
                for func in service.funcs.values():
                    STMT("{0} : (_func_{0}, _unpack_{0}, {1}),", 
                        func.id, type_to_packer(func.type))
            SEP()
            with BLOCK("packed_exceptions = ", prefix = "{", suffix = "}"):
                for mem in service.types.values():
                    if isinstance(mem, compiler.Exception):
                        STMT("{0} : {1},", mem.name, type_to_packer(mem))
            SEP()
            STMT("proc.post_init(func_mapping, packed_exceptions, exception_map)")
            STMT("proc.handshake(AGNOS_VERSION, IDL_MAGIC)")
            STMT("return proc")
    
    def _generate_processor_function(self, module, func):
        BLOCK = module.block
        STMT = module.stmt
        SEP = module.sep
        
        if isinstance(func, compiler.Func):
            with BLOCK("def _func_{0}(args)", func.id):
                STMT("return handler.{0}(*args)", func.fullname) 
        else:
            with BLOCK("def _func_{0}(args)", func.id):
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

    def _generate_processor_unpacker(self, module, func):
        BLOCK = module.block
        STMT = module.stmt
        SEP = module.sep
        
        with BLOCK("def _unpack_{0}(stream)", func.id):
            if not func.args:
                STMT("return []")
                return 
            with BLOCK("return ", prefix = "[", suffix="]"):
                for arg in func.args:
                    STMT("{0}.unpack(stream),", type_to_packer(arg.type))
    
    def generate_client(self, module, service):
        BLOCK = module.block
        STMT = module.stmt
        SEP = module.sep
        
        with BLOCK("def Client(instream, outstream)"):
            with BLOCK("class ClientClass(agnos.BaseClient)"):
                with BLOCK("PACKED_EXCEPTIONS = ", prefix = "{", suffix = "}"):
                    for mem in service.types.values():
                        if isinstance(mem, compiler.Exception):
                            STMT("{0} : {1},", mem.id, type_to_packer(mem))
                SEP()
                with BLOCK("def __init__(self, instream, outstream)"):
                    STMT("agnos.BaseClient.__init__(self, instream, outstream)")
                    for func in service.funcs.values():
                        if not func.namespace:
                            continue
                        STMT("self.{0} = agnos.Namespace()", func.namespace.split(".")[0])
                    for func in service.funcs.values():
                        if not func.namespace:
                            continue
                        head, tail = (func.namespace + "." + func.name).split(".", 1)
                        STMT("self.{0}['{1}'] = self._autogen_{2}", head, tail, func.fullname)
                SEP()
                with BLOCK("def _handshake(self)"):
                    STMT("magic = packers.Int32.unpack(self._instream)")
                    with BLOCK("if magic != agnos.AGNOS_MAGIC"):
                        STMT("raise agnos.HandshakeError('Wrong magic: 0x%08x' % (magic,))")
                    STMT("version = packers.Str.unpack(self._instream)")
                    with BLOCK("if version != AGNOS_VERSION"):
                        STMT("raise agnos.HandshakeError('Wrong version of Agnos: %r' % (version,))")
                    STMT("idlmagic = packers.Str.unpack(self._instream)")
                    with BLOCK("if idlmagic != IDL_MAGIC"):
                        STMT("raise agnos.HandshakeError('Wrong IDL magic: %r' % (idlmagic,))")
                    with BLOCK("with self._outstream.transaction() as trans"):
                        STMT("packers.Str.pack(trans, 'OK')")
                SEP()
                for func in service.funcs.values():
                    args = ", ".join(arg.name for arg in func.args)
                    if func.namespace:
                        name = "_autogen_%s" % (func.fullname,)
                    else:
                        name = func.name
                    with BLOCK("def {0}_send(_self, {1})", name, args):
                        with BLOCK("with _self._outstream.transaction() as trans"):
                            STMT("seq = _self._send_invocation(trans, {0}, {1})", func.id, type_to_packer(func.type))
                            for arg in func.args:
                                STMT("{0}.pack({1}, trans)", type_to_packer(arg.type), arg.name)
                        STMT("return seq")
                    with BLOCK("def {0}(_self, {1})", name, args):
                        STMT("seq = _self.{0}_send({1})", name, args)
                        STMT("return _self._get_reply(seq)")
                    SEP()
            STMT("clnt = ClientClass(instream, outstream)")
            STMT("storer = lambda proxy: proxy._objref")
            SEP()
            for tp in service.types.values():
                if isinstance(tp, compiler.Class):
                    STMT("{0}ObjRef = packers.ObjRef(storer, lambda oid: clnt._get_proxy({0}Proxy, oid))", tp.name)
            SEP()
            for member in service.types.values():
                if isinstance(member, compiler.Record):
                    if is_complex_type(member):
                        self.generate_record_packer(module, member)
                        SEP()
            self.generate_templated_packers(module, service)
            STMT("return clnt")
        SEP()
        STMT("@utils.make_method(Client)")
        with BLOCK("def from_transport(transport)"):
            STMT("return Client(transport.get_input_stream(), transport.get_output_stream())")
        SEP()
        STMT("@utils.make_method(Client)")
        with BLOCK("def connect(host, port)"):
            STMT("return Client.from_transport(agnos.SocketTransport.connect(host, port))")
        SEP()
        STMT("@utils.make_method(Client)")
        with BLOCK("def connect_executable(filename, args = None)"):
            STMT("transport = agnos.ProcTransport.from_executable(filename, args)")
            STMT("return Client.from_transport(transport)")
        SEP()
        STMT("@utils.make_method(Client)")
        with BLOCK("def connect_proc(proc)"):
            STMT("transport = agnos.ProcTransport.from_proc(proc)")
            STMT("return Client.from_transport(transport)")







