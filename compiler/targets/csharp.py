from contextlib import contextmanager
from .base import TargetBase
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
    elif t == compiler.t_objref:
        return "long" 
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
    if t == compiler.t_bool:
        return "Packers.Bool"
    if t == compiler.t_int8:
        return "Packers.Int8"
    if t == compiler.t_int16:
        return "Packers.Int16"
    if t == compiler.t_int32:
        return "Packers.Int32"
    if t == compiler.t_int64:
        return "Packers.Int64"
    if t == compiler.t_float:
        return "Packers.Float"
    if t == compiler.t_date:
        return "Packers.Date"
    if t == compiler.t_buffer:
        return "Packers.Buffer"
    if t == compiler.t_string:
        return "Packers.Str"
    elif t == compiler.t_objref:
        return type_to_packer(compiler.t_int64) 
    if isinstance(t, (compiler.Record, compiler.Exception)):
        return "%sRecord" % (t.name,)
    if isinstance(t, compiler.Enum):
        return type_to_packer(compiler.t_int32)
    if isinstance(t, compiler.Class):
        return type_to_packer(compiler.t_objref)
    return "%r$packer" % (t,)

def const_to_cs(typ, val):
    if val is None:
        return "null"
    if val is True:
        return "true"
    if val is False:
        return "false"
    elif isinstance(val, (int, long, float)):
        return str(val)
    elif isinstance(val, (str, unicode)):
        return repr(val)
    elif isinstance(val, list):
        return "$const-list"
        #return "new ArrayList<%s>{{%s}}" % (typ.oftype, body,)
    elif isinstance(val, dict):
        return "$const-map"
    else:
        raise IDLError("%r cannot be converted to a cs const" % (val,))


class CSharpTarget(TargetBase):
    DEFAULT_TARGET_DIR = "gen-csharp"

    @contextmanager
    def new_module(self, filename):
        mod = clike.Module()
        yield mod
        with self.open(filename, "w") as f:
            f.write(mod.render())

    def generate(self, service):
        with self.new_module("%s.cs" % (service.name,)) as module:
            BLOCK = module.block
            STMT = module.stmt
            SEP = module.sep
            DOC = module.doc
            
            STMT("using System")
            STMT("using System.IO")
            STMT("using System.Collections.Generic")
            STMT("using Agnos")
            SEP()
            with BLOCK("namespace {0}Stub", service.name):
                with BLOCK("public static class {0}", service.name):
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

    def generate_enum(self, module, enum):
        BLOCK = module.block
        STMT = module.stmt
        SEP = module.sep

        with BLOCK("public enum {0}", enum.name):
            for mem in enum.members[:-1]:
                STMT("{0} = {1},", mem.name, mem.value, colon = False)
            STMT("{0} = {1}", enum.members[-1].name, enum.members[-1].value, colon = False)

    def generate_record(self, module, rec):
        BLOCK = module.block
        STMT = module.stmt
        SEP = module.sep

        is_exc = isinstance(rec, compiler.Exception)
        
        with BLOCK("public class {0}{1}", rec.name, " : PackedException" if is_exc else ""):
            STMT("protected const int __record_id = {0}", rec.id)
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
            with BLOCK("public {0}void pack(Stream stream)", "override " if is_exc else ""):
                STMT("Packers.Int32.pack(__record_id, stream)")
                STMT("{0}Record.pack(this, stream)", rec.name)
            SEP()
            with BLOCK("public override String ToString()"):
                STMT('return "{0}(" + {1} + ")"', rec.name, ' + ", " + '.join(mem.name  for mem in rec.members))
        SEP()

        with BLOCK("internal class _{0}Record : Packers.IPacker", rec.name):
            with BLOCK("public void pack(object obj, Stream stream)"):
                STMT("{0} val = ({0})obj", rec.name)
                for mem in rec.members:
                    #if isinstance(mem.type, compiler.Enum):
                    #    STMT("Packers.Int32.pack(val.{0}.value, stream)", mem.name)
                    #else:
                    STMT("{0}.pack(val.{1}, stream)", type_to_packer(mem.type), mem.name)

            with BLOCK("public object unpack(Stream stream)"):
                args = []
                for mem in rec.members:
                    #if isinstance(mem.type, compiler.Enum):
                    #    args.append("%s.getByValue((Integer)Packers.Int32.unpack(stream))" % (type_to_cs(mem.type),))
                    #else:
                    args.append("(%s)%s.unpack(stream)" % (type_to_cs(mem.type), type_to_packer(mem.type)))
                STMT("return new {0}({1})", rec.name, ", ".join(args))
        SEP()
        STMT("internal static _{0}Record {0}Record = new _{0}Record()", rec.name)

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
                            STMT("return _client._{0}_get_{1}(this)", cls.name, attr.name)
                    if attr.set:
                        with BLOCK("set"):
                            STMT("_client._{0}_set_{1}(this, value)", cls.name, attr.name)
            SEP()
            for method in cls.methods:
                args = ", ".join("%s %s" % (type_to_cs(arg.type, proxy = True), arg.name) for arg in method.args)
                with BLOCK("public {0} {1}({2})", type_to_cs(method.type, proxy = True), method.name, args):
                    callargs = ["this"] + [arg.name for arg in method.args]
                    if method.type == compiler.t_void:
                        STMT("_client._{0}_{1}({2})", cls.name, method.name, ", ".join(callargs))
                    else:
                        STMT("return _client._{0}_{1}({2})", cls.name, method.name, ", ".join(callargs))

    def generate_handler_interface(self, module, service):
        BLOCK = module.block
        STMT = module.stmt
        SEP = module.sep

        with BLOCK("public interface IHandler"):
            for member in service.funcs.values():
                if isinstance(member, compiler.Func):
                    args = ", ".join("%s %s" % (type_to_cs(arg.type), arg.name) for arg in member.args)
                    STMT("{0} {1}({2})", type_to_cs(member.type), member.name, args)

    def generate_processor(self, module, service):
        BLOCK = module.block
        STMT = module.stmt
        SEP = module.sep

        funcs = [mem for mem in service.funcs.values()
            if isinstance(mem, (compiler.Func, compiler.AutoGeneratedFunc))]

        with BLOCK("public class Processor : Protocol.BaseProcessor"):
            STMT("protected IHandler handler")
            SEP()
            with BLOCK("public Processor(IHandler handler) : base()"):
                STMT("this.handler = handler")
            SEP()
            with BLOCK("protected override void process_invoke(Stream inStream, Stream outStream, int seq)"):
                STMT("int funcid = (int){0}.unpack(inStream)", type_to_packer(compiler.t_int32))
                STMT("Packers.IPacker packer = null")
                STMT("object result = null")
                STMT("long id")
                with BLOCK("switch (funcid)"):
                    for func in funcs:
                        with BLOCK("case {0}:", func.id, prefix = None, suffix = None):
                            if isinstance(func, compiler.Func):
                                args = []
                                for arg in func.args:
                                    if isinstance(arg.type, compiler.Class):
                                        args.append("(%s)(load((long)Packers.Int64.unpack(inStream)))" % (type_to_cs(arg.type)))
                                    else:
                                        args.append("(%s)(%s.unpack(inStream))" % (type_to_cs(arg.type), type_to_packer(arg.type)))
                                if func.type == compiler.t_void:
                                    STMT("handler.{0}({1})", func.name, ", ".join(args))
                                else:
                                    STMT("result = handler.{0}({1})", func.name, ", ".join(args))
                            else:
                                args = []
                                for arg in func.args[1:]:
                                    if isinstance(arg.type, compiler.Class):
                                        args.append("(%s)(load((long)Packers.Int64.unpack(inStream)))" % (type_to_cs(arg.type)))
                                    else:
                                        args.append("(%s)(%s.unpack(inStream))" % (type_to_cs(arg.type), type_to_packer(arg.type)))
                                STMT("id = (long)(Packers.Int64.unpack(inStream))")
                                if isinstance(func.origin, compiler.ClassAttr):
                                    if "_get_" in func.name:
                                        STMT("result = (({0})load(id)).{1}", type_to_cs(func.origin.parent), func.origin.name)
                                    else:
                                        STMT("(({0})load(id)).{1} = {2}", type_to_cs(func.origin.parent), func.origin.name, args[0])
                                else:
                                    if func.type == compiler.t_void:
                                        STMT("(({0})load(id)).{1}({2})", type_to_cs(func.origin.parent), func.origin.name, ", ".join(args))
                                    else:
                                        STMT("result = (({0})load(id)).{1}({2})", type_to_cs(func.origin.parent), func.origin.name, ", ".join(args))
                            if isinstance(func.type, compiler.Class):
                                STMT("result = store(result)")
                            if func.type != compiler.t_void:
                                STMT("packer = {0}", type_to_packer(func.type))
                            STMT("break")
                    with BLOCK("default:", prefix = None, suffix = None):
                        STMT('throw new ProtocolError("unknown function id: " + funcid)')
                SEP()
                STMT("{0}.pack(seq, outStream)", type_to_packer(compiler.t_int32))
                STMT("{0}.pack((byte)Agnos.Protocol.REPLY_SUCCESS, outStream)", type_to_packer(compiler.t_int8))
                with BLOCK("if (packer != null)"):
                    STMT("packer.pack(result, outStream)")
                STMT("outStream.Flush()")

    def generate_client(self, module, service):
        BLOCK = module.block
        STMT = module.stmt
        SEP = module.sep

        with BLOCK("public class Client : Protocol.BaseClient"):
            with BLOCK("public Client(Stream inStream, Stream outStream) : base(inStream, outStream)"):
                pass
            with BLOCK("public Client(Agnos.Transports.ITransport transport) : base(transport)"):
                pass
            SEP()
            with BLOCK("internal new void _decref(long id)"):
                # to avoid protectedness issues
                STMT("base._decref(id)")
            SEP()
            with BLOCK("protected override PackedException _load_packed_exception()"):
                STMT("int clsid = (int)Packers.Int32.unpack(_inStream)")
                with BLOCK("switch (clsid)"):
                    for mem in service.types.values():
                        if not isinstance(mem, compiler.Exception):
                            continue
                        with BLOCK("case {0}:", mem.id, prefix = None, suffix = None):
                            STMT("return (PackedException)({0}Record.unpack(_inStream))", mem.name)
                    with BLOCK("default:", prefix = None, suffix = None):
                        STMT('throw new ProtocolError("unknown exception class id: " + clsid)')
            SEP()
            for func in service.funcs.values():
                if isinstance(func, compiler.Func):
                    access = "public"
                elif isinstance(func, compiler.AutoGeneratedFunc):
                    access = "internal"
                else:
                    continue
                args = ", ".join("%s %s" % (type_to_cs(arg.type, proxy = True), arg.name) for arg in func.args)
                with BLOCK("{0} {1} {2}({3})", access, type_to_cs(func.type, proxy = True), func.name, args):
                    STMT("_cmd_invoke({0})", func.id)
                    for arg in func.args:
                        if isinstance(arg.type, compiler.Class):
                            STMT("Packers.Int64.pack({0}._objref, _outStream)", arg.name)
                        else:
                            STMT("{0}.pack({1}, _outStream)", type_to_packer(arg.type), arg.name)
                    STMT("_outStream.Flush()")
                    if func.type == compiler.t_void:
                        STMT("_read_reply({0})", type_to_packer(func.type))
                    else:
                        STMT("object res = _read_reply({0})", type_to_packer(func.type))
                        if isinstance(func.type, compiler.Class):
                            STMT("return new {0}(this, (long)res)", type_to_cs(func.type, proxy = True))
                        else:
                            STMT("return ({0})res", type_to_cs(func.type))













