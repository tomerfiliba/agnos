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
    elif t == compiler.t_heteromap:
        return "Agnos.HeteroMap"
    elif isinstance(t, compiler.TList):
        return "IList"
    elif isinstance(t, compiler.TMap):
        return "IDictionary"
    elif isinstance(t, (compiler.Enum, compiler.Record, compiler.Exception)):
        return "%s" % (t.name,)
    elif isinstance(t, compiler.Class):
        if proxy:
            return "%sProxy" % (t.name,)
        else:
            return "I%s" % (t.name,)
    else:
        return "%s$$$type" % (t,)

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
    elif t == compiler.t_heteromap:
        return "heteroMapPacker"
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
            STMT("using System.Net")
            STMT("using System.Net.Sockets")
            STMT("using System.Diagnostics")
            STMT("using System.Collections")
            STMT("using System.Collections.Generic")
            STMT("using Agnos")
            STMT("using Agnos.Transports")
            SEP()
            with BLOCK("namespace {0}Bindings", service.name):
                with BLOCK("public static class {0}", service.name):
                    STMT('public const string AGNOS_VERSION = "Agnos 1.0"', service.digest)
                    STMT('public const string IDL_MAGIC = "{0}"', service.digest)
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
            return "new Packers.ListOf(%s, %s)" % (tp.id, self._generate_templated_packer_for_type(tp.oftype),)
        elif isinstance(tp, compiler.TMap):
            return "new Packers.MapOf(%s, %s, %s)" % (tp.id, self._generate_templated_packer_for_type(tp.keytype),
                self._generate_templated_packer_for_type(tp.valtype))
        else:
            return type_to_packer(tp)

    def generate_templated_packers_decl(self, module, service):
        BLOCK = module.block
        STMT = module.stmt
        SEP = module.sep
        
        for tp in service.all_types:
            if isinstance(tp, (compiler.TList, compiler.TMap)):
                if is_complex_type(tp):
                    STMT("internal Packers.AbstractPacker _{0}", tp.stringify())
                else:
                    definition = self._generate_templated_packer_for_type(tp)
                    STMT("internal static Packers.AbstractPacker _{0} = {1}", tp.stringify(), definition)
            
    def generate_templated_packers_impl(self, module, service):
        BLOCK = module.block
        STMT = module.stmt
        SEP = module.sep
        
        for tp in service.all_types:
            if isinstance(tp, (compiler.TList, compiler.TMap)) and is_complex_type(tp):
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
        with BLOCK("internal class _{0}Packer : Packers.AbstractPacker", enum.name):
            with BLOCK("public override int getId()"):
                STMT("return {0}", enum.id)
            with BLOCK("public override void pack(object obj, Stream stream)"):
                STMT("Packers.Int32.pack((int)(({0})obj), stream)", enum.name)
            with BLOCK("public override object unpack(Stream stream)"):
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
            with BLOCK("public override string ToString()"):
                STMT('return "{0}(" + {1} + ")"', rec.name, ' + ", " + '.join(mem.name  for mem in rec.members))

    def generate_record_packer(self, module, rec, static):
        BLOCK = module.block
        STMT = module.stmt
        SEP = module.sep

        with BLOCK("internal class _{0}Packer : Packers.AbstractPacker", rec.name):
            if not static:
                complex_types = rec.get_complex_types()
                for tp in complex_types:
                    STMT("protected Packers.AbstractPacker {0}", type_to_packer(tp))
                args =  ", ".join("Packers.AbstractPacker %s" % (type_to_packer(tp),) for tp in complex_types)
                with BLOCK("public _{0}Packer({1})", rec.name, args):
                    for tp in complex_types:
                        STMT("this.{0} = {0}", type_to_packer(tp))
                SEP()

            with BLOCK("public override int getId()"):
                STMT("return {0}", rec.id)

            with BLOCK("public override void pack(object obj, Stream stream)"):
                STMT("{0} val = ({0})obj", rec.name)
                for mem in rec.members:
                    STMT("{0}.pack(val.{1}, stream)", type_to_packer(mem.type), mem.name)

            with BLOCK("public override object unpack(Stream stream)"):
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
            with BLOCK("protected BaseProxy(Client client, long objref, bool owns_ref)"):
                STMT("_client = client")
                STMT("_objref = objref")
                STMT("_disposed = owns_ref ? false : true")
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
                    STMT("_client._utils.Decref(_objref)")
            SEP()
            with BLOCK("public override string ToString()"):
                STMT('return base.ToString() + "<" + _objref + ">"')

    def generate_class_interface(self, module, cls):
        BLOCK = module.block
        STMT = module.stmt
        SEP = module.sep
        DOC = module.doc

        if cls.extends:
            extends = " : " + ", ".join("I%s" % (c.name,) for c in cls.extends)
        else:
            extends = ""

        with BLOCK("public interface I{0}{1}", cls.name, extends):
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
        DOC = module.doc

        with BLOCK("public class {0}Proxy : BaseProxy, I{0}", cls.name):
            with BLOCK("internal {0}Proxy(Client client, long objref, bool owns_ref) :"
                    " base(client, objref, owns_ref)", cls.name):
                pass
            SEP()
            for attr in cls.all_attrs:
                with BLOCK("public {0} {1}", type_to_cs(attr.type), attr.name):
                    if attr.get:
                        with BLOCK("get"):
                            STMT("return ({0})_client._funcs.sync_{1}(this)", type_to_cs(attr.type), attr.getter.id)
                    if attr.set:
                        with BLOCK("set"):
                            STMT("_client._funcs.sync_{0}(this, value)", attr.setter.id)
            SEP()
            for method in cls.all_methods:
                args = ", ".join("%s %s" % (type_to_cs(arg.type), arg.name) for arg in method.args)
                with BLOCK("public {0} {1}({2})", type_to_cs(method.type), method.name, args):
                    callargs = ["this"] + [
                        "(%s)%s" % (type_to_cs(arg.type, proxy=True), arg.name) 
                            if isinstance(arg.type, compiler.Class) else arg.name 
                        for arg in method.args]
                    if method.type == compiler.t_void:
                        STMT("_client._funcs.sync_{0}({1})", method.func.id, ", ".join(callargs))
                    else:
                        STMT("return _client._funcs.sync_{0}({1})", method.func.id, ", ".join(callargs))
            if cls.all_derived:
                SEP()
                DOC("downcasts")
                for cls2 in cls.all_derived:
                    with BLOCK("public {0} CastTo{1}()", type_to_cs(cls2, proxy = True), cls2.name):
                        STMT("return new {0}(_client, _objref, false)", type_to_cs(cls2, proxy = True))
            if cls.all_bases:
                SEP()
                DOC("upcasts")
                for cls2 in cls.all_bases:
                    with BLOCK("public {0} CastTo{1}()", type_to_cs(cls2, proxy = True), cls2.name):
                        STMT("return new {0}(_client, _objref, false)", type_to_cs(cls2, proxy = True))

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
            STMT("protected Packers.HeteroMapPacker heteroMapPacker")
            SEP()
            with BLOCK("public Processor(IHandler handler)"):
                STMT("this.handler = handler")
                for tp in service.types.values():
                    if isinstance(tp, compiler.Class):
                        STMT("{0}ObjRef = new Packers.ObjRef({1}, this)", tp.name, tp.id)
                for rec in generated_records:
                    complex_types = rec.get_complex_types()
                    STMT("{0}Packer = new _{0}Packer({1})", rec.name, ", ".join(type_to_packer(tp) for tp in complex_types))
                self.generate_templated_packers_impl(module, service)
                SEP()
                STMT("Dictionary<int, Packers.AbstractPacker> packersMap = new Dictionary<int, Packers.AbstractPacker>()")
                for tp in service.types.values():
                    STMT("packersMap[{0}] = {1}", tp.id, type_to_packer(tp))
                STMT("heteroMapPacker = new Packers.HeteroMapPacker(999, packersMap)")
                STMT("packersMap[999] = heteroMapPacker")
            SEP()
            self.generate_process_getinfo(module, service)
            SEP()
            self.generate_process_invoke(module, service)

    def generate_process_getinfo(self, module, service):
        BLOCK = module.block
        STMT = module.stmt
        SEP = module.sep
        
        with BLOCK("protected override void processGetGeneralInfo(HeteroMap map)"):
            STMT('map["AGNOS_VERSION"] = AGNOS_VERSION')
            STMT('map["IDL_MAGIC"] = IDL_MAGIC')
            STMT('map["SERVICE_NAME"] = "{0}"', service.name)
        SEP()
        with BLOCK("protected override void processGetFunctionsInfo(HeteroMap map)"):
            STMT("HeteroMap funcinfo")
            STMT("Dictionary<string, string> args")
            STMT("Dictionary<string, string> anno")
            SEP()
            for func in service.funcs.values():
                STMT("funcinfo = new HeteroMap()")
                STMT('funcinfo["name"] = "{0}"', func.name)
                STMT('funcinfo["type"] = "{0}"', str(func.type))
                STMT("args = new Dictionary<string, string>()")
                for arg in func.args:
                    STMT('args["{0}"] = "{1}"', arg.name, str(arg.type))
                STMT('funcinfo.Add("args", args, Packers.mapOfStrStr)')
                if func.annotations:
                    STMT("anno = new Dictionary<string, string>()")
                    for anno in func.annotations:
                        STMT('anno["{0}"] = "{1}"', anno.name, anno.value)
                    STMT('funcinfo.Add("annotations", anno, Packers.mapOfStrStr)')
                STMT('map.Add({0}, funcinfo, Packers.builtinHeteroMapPacker)', func.id)
        SEP()
        with BLOCK("protected override void processGetFunctionCodes(HeteroMap map)"):
            for func in service.funcs.values():
                STMT('map["{0}"] = {1}', func.name, func.id)

    def generate_process_invoke(self, module, service):
        BLOCK = module.block
        STMT = module.stmt
        SEP = module.sep

        with BLOCK("override protected void processInvoke(ITransport transport, int seq)"):
            STMT("Packers.AbstractPacker packer = null")
            STMT("object result = null")
            STMT("object inst = null")
            STMT("object[] args = null")
            STMT("Stream stream = transport.GetStream()")
            STMT("int funcid = (int){0}.unpack(stream)", type_to_packer(compiler.t_int32))
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
                STMT("{0}.pack((byte)Protocol.REPLY_SUCCESS, stream)", type_to_packer(compiler.t_int8))
                with BLOCK("if (packer != null)"):
                    STMT("packer.pack(result, stream)")
            for tp in packed_exceptions:
                with BLOCK("catch ({0} ex)", tp.name):
                    STMT("transport.Reset()")
                    STMT("{0}.pack((byte)Protocol.REPLY_PACKED_EXCEPTION, stream)", type_to_packer(compiler.t_int8))
                    STMT("{0}.pack({1}, stream)", type_to_packer(compiler.t_int32), tp.id)
                    STMT("{0}.pack(ex, stream)", type_to_packer(tp))

    def generate_invocation_case(self, module, func):
        BLOCK = module.block
        STMT = module.stmt
        SEP = module.sep
        
        if isinstance(func, compiler.Func):
            if func.args:
                with BLOCK("args = new object[] {0}", "{", prefix = "", suffix = "};"):
                    for arg in func.args[:-1]:
                        STMT("{0}.unpack(stream)", type_to_packer(arg.type), suffix = ",")
                    if func.args:
                        arg = func.args[-1]
                        STMT("{0}.unpack(stream)", type_to_packer(arg.type), suffix = ",")
            callargs = ", ".join("(%s)args[%s]" % (type_to_cs(arg.type), i) for i, arg in enumerate(func.args))
            if func.type == compiler.t_void:
                invocation = "handler.%s(%s)" % (func.fullname, callargs) 
            else:
                invocation = "result = handler.%s(%s)" % (func.fullname, callargs)
        else:
            insttype = func.args[0].type
            STMT("inst = ({0})({1}.unpack(stream))", 
                type_to_cs(insttype), type_to_packer(insttype))

            if len(func.args) > 1:
                with BLOCK("args = new object[] {0}", "{", prefix = "", suffix = "};"):
                    for arg in func.args[1:-1]:
                        STMT("{0}.unpack(stream)", type_to_packer(arg.type), suffix = ",")
                    arg = func.args[-1]
                    STMT("{0}.unpack(stream)", type_to_packer(arg.type), suffix = ",")
            callargs = ", ".join("(%s)args[%s]" % (type_to_cs(arg.type), i) 
                for i, arg in enumerate(func.args[1:]))
            
            if isinstance(func.origin, compiler.ClassAttr):
                if func.type == compiler.t_void:
                    invocation = "((%s)inst).%s = (%s)args[0]" % (type_to_cs(insttype), func.origin.name, type_to_cs(func.origin.type))
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

    #===========================================================================
    # client
    #===========================================================================

    def generate_client(self, module, service):
        BLOCK = module.block
        STMT = module.stmt
        SEP = module.sep
        DOC = module.doc
        
        with BLOCK("public class Client : Protocol.BaseClient"):
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
                    STMT("object proxy = client._utils.GetProxy(id)")
                    with BLOCK("if (proxy == null)"):
                        STMT("proxy = newProxy(id)")
                        STMT("client._utils.CacheProxy(id, proxy)")
                    STMT("return proxy")
                STMT("protected abstract object newProxy(long id)")
            SEP()
            for tp in service.types.values():
                if isinstance(tp, compiler.Class):
                    with BLOCK("internal class {0}ClientSerializer : ClientSerializer", tp.name):
                        with BLOCK("public {0}ClientSerializer(Client client) : base(client)", tp.name):
                            pass
                        with BLOCK("protected override object newProxy(long id)"):
                            STMT("return new {0}(client, id, true)", type_to_cs(tp, proxy = True))
            SEP()
            STMT("protected Packers.HeteroMapPacker heteroMapPacker")
            SEP()
            namespaces = self.generate_client_namespaces(module, service)
            SEP()
            self.generate_client_internal_funcs(module, service)
            SEP()
            self.generate_client_ctor(module, service, namespaces, generated_records)
            SEP()
            self.generate_client_funcs(module, service)
            SEP()
            self.generate_client_factories(module, service)

    def generate_client_ctor(self, module, service, namespaces, generated_records):
        BLOCK = module.block
        STMT = module.stmt
        SEP = module.sep
        DOC = module.doc
        
        with BLOCK("public Client(ITransport transport)"):
            STMT("Dictionary<int, Packers.AbstractPacker> pem = new Dictionary<int, Packers.AbstractPacker>()") 
            STMT("_utils = new Protocol.ClientUtils(transport, pem)")
            STMT("_funcs = new _Functions(this)")
            SEP()
            for tp in service.types.values():
                if isinstance(tp, compiler.Class):
                    STMT("{0}ObjRef = new Packers.ObjRef({1}, new {0}ClientSerializer(this))", tp.name, tp.id) 
            
            for rec in generated_records:
                complex_types = rec.get_complex_types()
                STMT("{0}Packer = new _{0}Packer({1})", rec.name, ", ".join(type_to_packer(tp) for tp in complex_types))
            SEP()
            
            for mem in service.types.values():
                if isinstance(mem, compiler.Exception):
                    STMT("pem[{0}] = {1}Packer", mem.id, mem.name)
            SEP()
            
            for name, id in namespaces:
                STMT("{0} = new _Namespace{1}(_funcs)", name, id)
            
            self.generate_templated_packers_impl(module, service)
            SEP()
            
            STMT("Dictionary<int, Packers.AbstractPacker> packersMap = new Dictionary<int, Packers.AbstractPacker>()")
            for tp in service.types.values():
                STMT("packersMap[{0}] = {1}", tp.id, type_to_packer(tp))
            STMT("heteroMapPacker = new Packers.HeteroMapPacker(999, packersMap)")
            STMT("packersMap[999] = heteroMapPacker")

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
            STMT("internal _Functions _funcs")
            SEP()
            for name, node in root.iteritems():
                if isinstance(node, dict):
                    self.generate_client_namespace_classes(module, node)
                    subnamespaces.append((name, node["__id__"]))
                elif isinstance(node, compiler.Func):
                    func = node
                    args = ", ".join("%s %s" % (type_to_cs(arg.type, proxy = True), arg.name) for arg in func.args)
                    callargs = ", ".join(arg.name for arg in func.args)
                    with BLOCK("public {0} {1}({2})", type_to_cs(func.type, proxy = True), func.name, args):
                        if func.type == compiler.t_void:
                            STMT("_funcs.sync_{0}({1})", func.id, callargs)
                        else:
                            STMT("return _funcs.sync_{0}({1})", func.id, callargs)
            SEP()
            with BLOCK("internal _Namespace{0}(_Functions funcs)", root["__id__"]):
                STMT("_funcs = funcs")
                for name, id in subnamespaces:
                    STMT("{0} = new _Namespace{1}(funcs)", name, id)
        STMT("public _Namespace{0} {1}", root["__id__"], root["__name__"])

    def generate_client_factories(self, module, service):
        BLOCK = module.block
        STMT = module.stmt
        SEP = module.sep
        
        with BLOCK("public static Client ConnectSock(string host, int port)"):
            STMT("return new Client(new SocketTransport(host, port))")
        with BLOCK("public static Client ConnectSock(Socket sock)"):
            STMT("return new Client(new SocketTransport(sock))")
        
        with BLOCK("public static Client ConnectProc(string executable)"):
            STMT("return new Client(ProcTransport.Connect(executable))")
        with BLOCK("public static Client ConnectProc(Process proc)"):
            STMT("return new Client(ProcTransport.Connect(proc))")

        with BLOCK("public static Client ConnectUri(string uri)"):
            STMT("return new Client(new HttpClientTransport(uri))")
        with BLOCK("public static Client ConnectUri(Uri uri)"):
            STMT("return new Client(new HttpClientTransport(uri))")
    
    def generate_client_internal_funcs(self, module, service):
        BLOCK = module.block
        STMT = module.stmt
        SEP = module.sep
        DOC = module.doc
        with BLOCK("internal class _Functions"):
            STMT("internal Client client")
            with BLOCK("public _Functions(Client client)"):
                STMT("this.client = client")
            SEP()
            for func in service.funcs.values():
                args = ", ".join("%s %s" % (type_to_cs(arg.type, proxy = True), arg.name) for arg in func.args)
                with BLOCK("public {0} sync_{1}({2})", type_to_cs(func.type, proxy = True), func.id, args):
                    if is_complex_type(func.type):
                        STMT("int seq = client._utils.BeginCall({0}, client.{1})", func.id, type_to_packer(func.type))
                    else:
                        STMT("int seq = client._utils.BeginCall({0}, {1})", func.id, type_to_packer(func.type))
                    if func.args:
                        STMT("Stream stream = client._utils.transport.GetStream()")
                        with BLOCK("try"):
                            for arg in func.args:
                                if is_complex_type(arg.type):
                                    STMT("client.{0}.pack({1}, stream)", type_to_packer(arg.type), arg.name)
                                else:
                                    STMT("{0}.pack({1}, stream)", type_to_packer(arg.type), arg.name)
                        with BLOCK("catch (Exception ex)"):
                            STMT("client._utils.CancelCall()")
                            STMT("throw ex")
                    STMT("client._utils.EndCall()")
                    if func.type == compiler.t_void:
                        STMT("client._utils.GetReply(seq)")
                    else:
                        STMT("return ({0})client._utils.GetReply(seq)", type_to_cs(func.type, proxy = True))
                SEP()
        SEP()
        STMT("internal _Functions _funcs")
    
    def generate_client_funcs(self, module, service):
        BLOCK = module.block
        STMT = module.stmt
        SEP = module.sep
        DOC = module.doc
        for func in service.funcs.values():
            if not isinstance(func, compiler.Func) or func.namespace:
                continue
            args = ", ".join("%s %s" % (type_to_cs(arg.type, proxy = True), arg.name) for arg in func.args)
            callargs = ", ".join(arg.name for arg in func.args)
            with BLOCK("public {0} {1}({2})", type_to_cs(func.type, proxy = True), func.name, args):
                if func.type == compiler.t_void:
                    STMT("_funcs.sync_{0}({1})", func.id, callargs)
                else:
                    STMT("return _funcs.sync_{0}({1})", func.id, callargs)
            SEP()











