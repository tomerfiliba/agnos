import itertools
from contextlib import contextmanager
from .base import TargetBase, is_complex_type, NOOP
from ..langs import clike
from .. import compiler


def type_to_cs(t, proxy = False):
    if t == compiler.t_void:
        return "void"
    elif t == compiler.t_bool:
        return "bool"
    elif t == compiler.t_int8:
        return "byte"
    elif t == compiler.t_int16:
        return "short"
    elif t == compiler.t_int32:
        return "int"
    elif t == compiler.t_int64:
        return "long"
    elif t == compiler.t_float:
        return "double"
    elif t == compiler.t_string:
        return "string"
    elif t == compiler.t_date:
        return "DateTime"
    elif t == compiler.t_buffer:
        return "byte[]"
    elif isinstance(t, compiler.TList):
        return "List<%s>" % (type_to_cs(t.oftype, proxy = proxy),)
    elif isinstance(t, compiler.TMap):
        return "Dictionary<%s, %s>" % (
            type_to_cs(t.keytype, proxy = proxy), 
            type_to_cs(t.valtype, proxy = proxy))
    elif isinstance(t, (compiler.Enum, compiler.Record, compiler.Exception)):
        return "%s" % (t.name,)
    elif isinstance(t, compiler.Class):
        if proxy:
            return "%sProxy" % (t.name,)
        else:
            return "I%s" % (t.name,)
    else:
        return "%r$type" % (t,)

def type_to_packer(t):
    if t == compiler.t_void:
        return "null"
    elif t == compiler.t_bool:
        return "Packers.Bool"
    elif t == compiler.t_int8:
        return "Packers.Int8"
    elif t == compiler.t_int16:
        return "Packers.Int16"
    elif t == compiler.t_int32:
        return "Packers.Int32"
    elif t == compiler.t_int64:
        return "Packers.Int64"
    elif t == compiler.t_float:
        return "Packers.Float"
    elif t == compiler.t_date:
        return "Packers.Date"
    elif t == compiler.t_buffer:
        return "Packers.Buffer"
    elif t == compiler.t_string:
        return "Packers.Str"
    elif isinstance(t, (compiler.TList, compiler.TMap)):
        return "_%s" % (t.stringify(),)
    elif isinstance(t, (compiler.Enum, compiler.Record, compiler.Exception)):
        return "%sPacker" % (t.name,)
    elif isinstance(t, compiler.Class):
        return "%sObjRef" % (t.name,)
    return "%r$$$packer" % (t,)

def const_to_cs(typ, val):
    if val is None:
        return "null"
    elif typ == compiler.t_bool:
        if val:
            return "true"
        else:
            return "false"
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
    #elif isinstance(val, list):
    #    return "$const-list %r" % (val,)
    #    #return "new ArrayList<%s>{{%s}}" % (typ.oftype, body,)
    #elif isinstance(val, dict):
    #    return "$const-map %r " % (val,)
    else:
        raise IDLError("%r cannot be converted to a c# const" % (val,))


temp_counter = itertools.count(7081)


class CSharpTarget(TargetBase):
    DEFAULT_TARGET_DIR = "."

    @contextmanager
    def new_module(self, filename):
        mod = clike.Module()
        yield mod
        with self.open(filename, "w") as f:
            f.write(mod.render())

    def generate(self, service):
        with self.new_module("%sBindings.cs" % (service.name,)) as module:
            BLOCK = module.block
            STMT = module.stmt
            SEP = module.sep
            DOC = module.doc
            
            STMT("using System")
            STMT("using System.IO")
            STMT("using System.Collections.Generic")
            STMT("using Agnos")
            SEP()
            with BLOCK("namespace {0}Bindings", service.name):
                with BLOCK("public static class {0}", service.name):
                    STMT('private const string _IDL_MAGIC = "{0}"', service.digest)
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
                                self.generate_record_packer(module, member, static = True)
                                SEP()
    
                    DOC("consts", spacer = True)
                    for member in service.consts.values():
                        STMT("public const {0} {1} = {2}", type_to_cs(member.type), 
                            member.name, const_to_cs(member.type, member.value))
                    SEP()
                    
                    DOC("classes", spacer = True)
                    self.generate_base_class_proxy(module, service)
                    SEP()
                    for member in service.types.values():
                        if isinstance(member, compiler.Class):
                            self.generate_class_interface(module, member)
                            SEP()
                            self.generate_class_proxy(module, service, member)
                            SEP()
    
                    DOC("server implementation", spacer = True)
                    self.generate_handler_interface(module, service)
                    SEP()
                    self.generate_processor(module, service)
                    SEP()
    
                    DOC("client", spacer = True)
                    self.generate_client(module, service)
                    SEP()

    def _generate_templated_packer_for_type(self, tp):
        if isinstance(tp, compiler.TList):
            return "new Packers.ListOf(%s)" % (self._generate_templated_packer_for_type(tp.oftype),)
        elif isinstance(tp, compiler.TMap):
            return "new Packers.MapOf(%s, %s)" % (self._generate_templated_packer_for_type(tp.keytype),
                self._generate_templated_packer_for_type(tp.valtype))
        else:
            return type_to_packer(tp)

    def generate_templated_packers_decl(self, module, service):
        BLOCK = module.block
        STMT = module.stmt
        SEP = module.sep
        
        for tp in service.all_types:
            if isinstance(tp, (compiler.TList, compiler.TMap)):
                STMT("internal Packers.IPacker _{0}", tp.stringify())

    def generate_templated_packers_impl(self, module, service):
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

        with BLOCK("public enum {0}", enum.name):
            for mem in enum.members[:-1]:
                STMT("{0} = {1}", mem.name, mem.value, suffix = ",")
            STMT("{0} = {1}", enum.members[-1].name, enum.members[-1].value, suffix = "")
        SEP()
        with BLOCK("internal class _{0}Packer : Packers.IPacker", enum.name):
            with BLOCK("public void pack(object obj, Stream stream)"):
                STMT("Packers.Int32.pack((int)(({0})obj), stream)", enum.name)
            with BLOCK("public object unpack(Stream stream)"):
                STMT("return ({0})((int)Packers.Int32.unpack(stream))", enum.name)
        SEP()
        STMT("internal static _{0}Packer {0}Packer = new _{0}Packer()", enum.name)

    def generate_record_class(self, module, rec):
        BLOCK = module.block
        STMT = module.stmt
        SEP = module.sep

        is_exc = isinstance(rec, compiler.Exception)

        with BLOCK("public class {0}{1}", rec.name, " : PackedException" if is_exc else ""):
            STMT("internal const int __recid = {0}", rec.id)
            for mem in rec.members:
                STMT("public {0} {1}", type_to_cs(mem.type), mem.name)
            SEP()
            with BLOCK("public {0}()", rec.name):
                pass
            args = ", ".join("%s %s" % (type_to_cs(mem.type), mem.name) for mem in rec.members)
            with BLOCK("public {0}({1})", rec.name, args):
                for mem in rec.members:
                    STMT("this.{0} = {0}", mem.name)
            SEP()
            with BLOCK("public override String ToString()"):
                STMT('return "{0}(" + {1} + ")"', rec.name, ' + ", " + '.join(mem.name  for mem in rec.members))

    def generate_record_packer(self, module, rec, static):
        BLOCK = module.block
        STMT = module.stmt
        SEP = module.sep

        with BLOCK("internal class _{0}Packer : Packers.IPacker", rec.name):
            if not static:
                complex_types = rec.get_complex_types()
                for tp in complex_types:
                    STMT("protected Packers.IPacker {0}", type_to_packer(tp))
                args =  ", ".join("Packers.IPacker %s" % (type_to_packer(tp),) for tp in complex_types)
                with BLOCK("public _{0}Packer({1})", rec.name, args):
                    for tp in complex_types:
                        STMT("this.{0} = {0}", type_to_packer(tp))
                SEP()
            with BLOCK("public void pack(object obj, Stream stream)"):
                STMT("{0} val = ({0})obj", rec.name)
                for mem in rec.members:
                    STMT("{0}.pack(val.{1}, stream)", type_to_packer(mem.type), mem.name)

            with BLOCK("public object unpack(Stream stream)"):
                with BLOCK("return new {0}(", rec.name, prefix = "", suffix = ");"):
                    for mem in rec.members[:-1]:
                        STMT("({0}){1}.unpack(stream)", type_to_cs(mem.type), 
                            type_to_packer(mem.type), suffix = ",")
                    if rec.members:
                        mem = rec.members[-1]
                        STMT("({0}){1}.unpack(stream)", type_to_cs(mem.type), 
                            type_to_packer(mem.type), suffix = "")
        SEP()
        if static:
            STMT("internal static _{0}Packer {0}Packer = new _{0}Packer()", rec.name)
        else:
            STMT("internal _{0}Packer {0}Packer", rec.name)

    def generate_base_class_proxy(self, module, service):
        BLOCK = module.block
        STMT = module.stmt
        SEP = module.sep

        with BLOCK("public abstract class BaseProxy : IDisposable"):
            STMT("internal long _objref")
            STMT("protected Client _client")
            STMT("protected bool _disposed")
            SEP()
            with BLOCK("protected BaseProxy(Client client, long objref)"):
                STMT("_client = client")
                STMT("_objref = objref")
                STMT("_disposed = false")
            SEP()
            with BLOCK("~BaseProxy()"):
                STMT("Dispose(false)")
            SEP()
            with BLOCK("public void Dispose()"):
                STMT("Dispose(true)")
                STMT("GC.SuppressFinalize(this)")
            with BLOCK("private void Dispose(bool disposing)"):
                with BLOCK("if (_disposed)"):
                    STMT("return")
                with BLOCK("lock (this)"):
                    STMT("_disposed = true")
                    STMT("_client._decref(_objref)")
            SEP()
            with BLOCK("public override String ToString()"):
                STMT('return base.ToString() + "<" + _objref + ">"')

    def generate_class_interface(self, module, cls):
        BLOCK = module.block
        STMT = module.stmt
        SEP = module.sep
        DOC = module.doc

        with BLOCK("public interface I{0}", cls.name):
            if cls.attrs:
                DOC("attributes")
            for attr in cls.attrs:
                with BLOCK("{0} {1}", type_to_cs(attr.type), attr.name):
                    if attr.get:
                        STMT("get")
                    if attr.set:
                        STMT("set")
            SEP()
            if cls.methods:
                DOC("methods")
            for method in cls.methods:
                args = ", ".join("%s %s" % (type_to_cs(arg.type), arg.name) for arg in method.args)
                STMT("{0} {1}({2})", type_to_cs(method.type), method.name, args)

    def generate_class_proxy(self, module, service, cls):
        BLOCK = module.block
        STMT = module.stmt
        SEP = module.sep

        with BLOCK("public class {0}Proxy : BaseProxy", cls.name):
            with BLOCK("internal {0}Proxy(Client client, long objref) : base(client, objref)", cls.name):
                pass
            SEP()
            for attr in cls.attrs:
                with BLOCK("public {0} {1}", type_to_cs(attr.type), attr.name):
                    if attr.get:
                        with BLOCK("get"):
                            STMT("return _client._autogen_{0}_get_{1}(this)", cls.name, attr.name)
                    if attr.set:
                        with BLOCK("set"):
                            STMT("_client._autogen_{0}_set_{1}(this, value)", cls.name, attr.name)
            SEP()
            for method in cls.methods:
                args = ", ".join("%s %s" % (type_to_cs(arg.type, proxy = True), arg.name) for arg in method.args)
                with BLOCK("public {0} {1}({2})", type_to_cs(method.type, proxy = True), method.name, args):
                    callargs = ["this"] + [arg.name for arg in method.args]
                    if method.type == compiler.t_void:
                        STMT("_client._autogen_{0}_{1}({2})", cls.name, method.name, ", ".join(callargs))
                    else:
                        STMT("return _client._autogen_{0}_{1}({2})", cls.name, method.name, ", ".join(callargs))

    def generate_handler_interface(self, module, service):
        BLOCK = module.block
        STMT = module.stmt
        SEP = module.sep

        with BLOCK("public interface IHandler"):
            for member in service.funcs.values():
                if isinstance(member, compiler.Func):
                    args = ", ".join("%s %s" % (type_to_cs(arg.type), arg.name) for arg in member.args)
                    STMT("{0} {1}({2})", type_to_cs(member.type), member.fullname, args)

    def generate_processor(self, module, service):
        BLOCK = module.block
        STMT = module.stmt
        SEP = module.sep

        with BLOCK("public class Processor : Protocol.BaseProcessor"):
            STMT("internal IHandler handler")
            SEP()
            for tp in service.types.values():
                if isinstance(tp, compiler.Class):
                    STMT("internal Packers.ObjRef {0}ObjRef", tp.name)
            SEP()
            generated_records = []
            for member in service.types.values():
                if isinstance(member, compiler.Record):
                    if is_complex_type(member):
                        self.generate_record_packer(module, member, static = False)
                        generated_records.append(member)
                        SEP()
            self.generate_templated_packers_decl(module, service)
            SEP()
            with BLOCK("public Processor(IHandler handler)"):
                STMT("this.handler = handler")
                for tp in service.types.values():
                    if isinstance(tp, compiler.Class):
                        STMT("{0}ObjRef = new Packers.ObjRef(this)", tp.name)
                for rec in generated_records:
                    complex_types = rec.get_complex_types()
                    STMT("{0}Packer = new _{0}Packer({1})", rec.name, ", ".join(type_to_packer(tp) for tp in complex_types))
                self.generate_templated_packers_impl(module, service)
            SEP()
            self.generate_process_invoke(module, service)

    def generate_process_invoke(self, module, service):
        BLOCK = module.block
        STMT = module.stmt
        SEP = module.sep

        with BLOCK("override protected void process_invoke(Stream inStream, Stream outStream, int seq)"):
            STMT("int funcid = (int){0}.unpack(inStream)", type_to_packer(compiler.t_int32))
            STMT("Packers.IPacker packer = null")
            STMT("object result = null")
            STMT("object inst = null")
            STMT("object[] args = null")
            packed_exceptions = [tp for tp in service.types.values() if isinstance(tp, compiler.Exception)]

            with BLOCK("try") if packed_exceptions else NOOP:
                with BLOCK("switch (funcid)"):
                    for func in service.funcs.values():
                        with BLOCK("case {0}:", func.id, prefix = None, suffix = None):
                            self.generate_invocation_case(module, func)
                            if func.type != compiler.t_void:
                                STMT("packer = {0}", type_to_packer(func.type))
                            STMT("break")
                    with BLOCK("default:", prefix = None, suffix = None):
                        STMT('throw new ProtocolError("unknown function id: " + funcid)')
                SEP()
                STMT("{0}.pack(seq, outStream)", type_to_packer(compiler.t_int32))
                STMT("{0}.pack((byte)Protocol.REPLY_SUCCESS, outStream)", type_to_packer(compiler.t_int8))
                with BLOCK("if (packer != null)"):
                    STMT("packer.pack(result, outStream)")
            for tp in packed_exceptions:
                with BLOCK("catch ({0} ex)", tp.name):
                    STMT("{0}.pack(seq, outStream)", type_to_packer(compiler.t_int32))
                    STMT("{0}.pack((byte)Protocol.REPLY_PACKED_EXCEPTION, outStream)", type_to_packer(compiler.t_int8))
                    STMT("{0}.pack({1}.__recid, outStream)", type_to_packer(compiler.t_int32), tp.name)
                    STMT("{0}.pack(ex, outStream)", type_to_packer(tp))

    def generate_invocation_case(self, module, func):
        BLOCK = module.block
        STMT = module.stmt
        SEP = module.sep
        
        if isinstance(func, compiler.Func):
            if func.args:
                with BLOCK("args = new object[] {0}", "{", prefix = "", suffix = "};"):
                    for arg in func.args[:-1]:
                        STMT("{0}.unpack(inStream)", type_to_packer(arg.type), suffix = ",")
                    if func.args:
                        arg = func.args[-1]
                        STMT("{0}.unpack(inStream)", type_to_packer(arg.type), suffix = ",")
            callargs = ", ".join("(%s)args[%s]" % (type_to_cs(arg.type), i) for i, arg in enumerate(func.args))
            if func.type == compiler.t_void:
                invocation = "handler.%s(%s)" % (func.fullname, callargs) 
            else:
                invocation = "result = handler.%s(%s)" % (func.fullname, callargs)
        else:
            insttype = func.args[0].type
            STMT("inst = ({0})({1}.unpack(inStream))", 
                type_to_cs(insttype), type_to_packer(insttype))

            if len(func.args) > 1:
                with BLOCK("args = new object[] {0}", "{", prefix = "", suffix = "};"):
                    for arg in func.args[1:-1]:
                        STMT("{0}.unpack(inStream)", type_to_packer(arg.type), suffix = ",")
                    arg = func.args[-1]
                    STMT("{0}.unpack(inStream)", type_to_packer(arg.type), suffix = ",")
            callargs = ", ".join("(%s)args[%s]" % (type_to_cs(arg.type), i) for i, arg in enumerate(func.args[1:]))
            
            if isinstance(func.origin, compiler.ClassAttr):
                if func.type == compiler.t_void:
                    invocation = "((%s)inst).%s = args[0]" % (type_to_cs(insttype), func.origin.name)
                else:
                    invocation = "result = ((%s)inst).%s" % (type_to_cs(insttype), func.origin.name)
            else:
                if func.type == compiler.t_void:
                    invocation = "((%s)inst).%s(%s)" % (type_to_cs(insttype), func.origin.name, callargs)
                else:
                    invocation = "result = ((%s)inst).%s(%s)" % (type_to_cs(insttype), func.origin.name, callargs)
        
        with BLOCK("try {0}", "{", prefix = ""):
            STMT(invocation)
        with BLOCK("catch (PackedException ex) {0}", "{", prefix = ""):
            STMT("throw ex")
        with BLOCK("catch (Exception ex) {0}", "{", prefix = ""):
            STMT("throw new GenericException(ex.Message, ex.StackTrace)")

    def generate_client_namespaces(self, module, service):
        nsid = itertools.count(0)
        root = {"__id__" : nsid.next()}
        for func in service.funcs.values():
            if isinstance(func, compiler.Func) and func.namespace:
                node = root
                fns = func.namespace.split(".")
                for part in fns:
                    if part not in node:
                        node[part] = {}
                        node[part]["__id__"] = nsid.next()
                        node[part]["__name__"] = part
                    node = node[part]
                node[func.name] = func
        roots = []
        for name, node in root.iteritems():
            if isinstance(node, dict):
                roots.append((name, node["__id__"]))
                self.generate_client_namespace_classes(module, node)
        return roots
    
    def generate_client_namespace_classes(self, module, root):
        BLOCK = module.block
        STMT = module.stmt
        SEP = module.sep
        with BLOCK("public class _Namespace{0}", root["__id__"]):
            subnamespaces = []
            STMT("internal Client client")
            SEP()
            for name, node in root.iteritems():
                if isinstance(node, dict):
                    self.generate_client_namespace_classes(module, node)
                    subnamespaces.append((name, node["__id__"]))
                elif isinstance(node, compiler.Func):
                    func = node
                    args = ", ".join("%s %s" % (type_to_cs(arg.type, proxy = True), arg.name) for arg in func.args)
                    with BLOCK("public {0} {1}({2})", type_to_cs(func.type, proxy = True), func.name, args):
                        if func.type == compiler.t_void:
                            STMT("client.{0}({1})", func.fullname, ", ".join(arg.name for arg in func.args))
                        else:
                            STMT("return client.{0}({1})", func.fullname, ", ".join(arg.name for arg in func.args))
            SEP()
            with BLOCK("internal _Namespace{0}(Client client)", root["__id__"]):
                STMT("this.client = client")
                for name, id in subnamespaces:
                    STMT("{0} = new _Namespace{1}(client)", name, id)
        STMT("public _Namespace{0} {1}", root["__id__"], root["__name__"])

    def generate_client(self, module, service):
        BLOCK = module.block
        STMT = module.stmt
        SEP = module.sep
        DOC = module.doc
        
        with BLOCK("public class Client : Protocol.BaseClient"):
            self.generate_client_packers(module, service)
            SEP()
            with BLOCK("public Client(Agnos.Transports.ITransport transport) : " +
                    "this(transport.getInputStream(), transport.getOutputStream())"):
                pass
            SEP()
            with BLOCK("internal new void _decref(long id)"):
                # to avoid protectedness issues
                STMT("base._decref(id)")
            SEP()
            with BLOCK("override protected PackedException _load_packed_exception()"):
                STMT("int clsid = (int)Packers.Int32.unpack(_inStream)")
                with BLOCK("switch (clsid)"):
                    for mem in service.types.values():
                        if not isinstance(mem, compiler.Exception):
                            continue
                        with BLOCK("case {0}:", mem.id, prefix = None, suffix = None):
                            STMT("return (PackedException)({0}Packer.unpack(_inStream))", mem.name)
                    with BLOCK("default:", prefix = None, suffix = None):
                        STMT('throw new ProtocolError("unknown exception class id: " + clsid)')
            SEP()
            self.generate_client_funcs(module, service)
    
    def generate_client_packers(self, module, service):
        BLOCK = module.block
        STMT = module.stmt
        SEP = module.sep
        DOC = module.doc
        
        for tp in service.types.values():
            if isinstance(tp, compiler.Class):
                STMT("internal Packers.ObjRef {0}ObjRef", tp.name)
        SEP()
        generated_records = []
        for member in service.types.values():
            if isinstance(member, compiler.Record):
                if is_complex_type(member):
                    self.generate_record_packer(module, member, static = False)
                    generated_records.append(member)
                    SEP()
        self.generate_templated_packers_decl(module, service)
        SEP()
        with BLOCK("internal abstract class ClientSerializer : Packers.ISerializer"):
            STMT("public Client client")
            SEP()
            with BLOCK("public ClientSerializer(Client client)"):
                STMT("this.client = client")
            SEP()
            with BLOCK("public long store(object obj)"):
                with BLOCK("if (obj == null)"):
                    STMT("return -1")
                STMT("return ((BaseProxy)obj)._objref")
            SEP()
            with BLOCK("public object load(long id)"):
                with BLOCK("if (id < 0)"):
                    STMT("return null")
                STMT("object proxy = client._get_proxy(id)")
                with BLOCK("if (proxy == null)"):
                    STMT("proxy = _new_proxy(id)")
                STMT("return proxy")
            STMT("protected abstract object _new_proxy(long id)")
        SEP()
        for tp in service.types.values():
            if isinstance(tp, compiler.Class):
                with BLOCK("internal class {0}ClientSerializer : ClientSerializer", tp.name):
                    with BLOCK("public {0}ClientSerializer(Client client) : base(client)", tp.name):
                        pass
                    with BLOCK("protected override object _new_proxy(long id)"):
                        STMT("return new {0}(client, id)", type_to_cs(tp, proxy = True))
        SEP()
        namespaces = self.generate_client_namespaces(module, service)
        SEP()
        with BLOCK("public Client(Stream inStream, Stream outStream) : base(inStream, outStream)"):
            for tp in service.types.values():
                if isinstance(tp, compiler.Class):
                    STMT("{0}ObjRef = new Packers.ObjRef(new {0}ClientSerializer(this))", tp.name) 
            if generated_records:
                SEP()
                for rec in generated_records:
                    complex_types = rec.get_complex_types()
                    STMT("{0}Packer = new _{0}Packer({1})", rec.name, ", ".join(type_to_packer(tp) for tp in complex_types))
            if namespaces:
                SEP()
                for name, id in namespaces:
                    STMT("{0} = new _Namespace{1}(this)", name, id)
            self.generate_templated_packers_impl(module, service)
    
    def generate_client_funcs(self, module, service):
        BLOCK = module.block
        STMT = module.stmt
        SEP = module.sep
        DOC = module.doc
        for func in service.funcs.values():
            if isinstance(func, compiler.Func) and not func.namespace:
                access = "public"
            else:
                access = "internal"

            args = ", ".join("%s %s" % (type_to_cs(arg.type, proxy = True), arg.name) for arg in func.args)
            with BLOCK("internal int {0}_send({1})", func.fullname, args):
                STMT("_sendBuffer.Position = 0")
                STMT("_sendBuffer.SetLength(0)")
                STMT("int seq = _send_invocation(_sendBuffer, {0}, {1})", func.id, type_to_packer(func.type))
                for arg in func.args:
                    STMT("{0}.pack({1}, _sendBuffer)", type_to_packer(arg.type), arg.name)
                STMT("_sendBuffer.WriteTo(_outStream)")
                STMT("_outStream.Flush()")
                STMT("return seq")
            SEP()
            #if access == "public":
            #    self.emit_func_javadoc(func, module)
            with BLOCK("{0} {1} {2}({3})", access, type_to_cs(func.type, proxy = True), func.fullname, args):
                STMT("int seq = {0}_send({1})", func.fullname, ", ".join(arg.name for arg in func.args))
                if func.type == compiler.t_void:
                    STMT("_get_reply(seq)")
                else:
                    STMT("return ({0})_get_reply(seq)", type_to_cs(func.type, proxy = True))
            SEP()
            # timed and async












