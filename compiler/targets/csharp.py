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
            STMT("using System.Collections.Generic")
            STMT("using Agnos")
            SEP()
            with BLOCK("namespace {0}", service.name):
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
                #for member in service.consts.values():
                #    STMT("public const {0} {1} = {2}", type_to_cs(member.type), 
                #        member.name, const_to_cs(member.type, member.value))
                #SEP()
                
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

        if isinstance(rec, compiler.Exception):
            extends = ": PackedException"
        else:
            extends = ""
        
        with BLOCK("public class {0} {1}", rec.name, extends):
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
            with BLOCK("public void pack(Stream stream)"):
                STMT("Packers.Int32.pack(__record_id, stream)")
                STMT("{0}Record.pack(this, stream)", rec.name)
            SEP()
            with BLOCK("public String toString()"):
                STMT('return "{0}(" + {1} + ")"', rec.name, ' + ", " + '.join(mem.name  for mem in rec.members))
        SEP()

        with BLOCK("internal class _{0}Record : Packers.IPacker", rec.name):
            with BLOCK("public void pack(Object obj, Stream stream)"):
                STMT("{0} val = ({0})obj", rec.name)
                for mem in rec.members:
                    #if isinstance(mem.type, compiler.Enum):
                    #    STMT("Packers.Int32.pack(val.{0}.value, stream)", mem.name)
                    #else:
                    STMT("{0}.pack(val.{1}, stream)", type_to_packer(mem.type), mem.name)

            with BLOCK("public Object unpack(InputStream stream) throws IOException"):
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
            STMT("protected long _objref")
            STMT("protected Client _client")
            STMT("protected bool _disposed")
            SEP()
            with BLOCK("protected BaseProxy(Service.Client client, Long objref)"):
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
            with BLOCK("public String ToString()"):
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

        with BLOCK("public class {0}Proxy : BaseProxy implements I{0}", cls.name):
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
                args = ", ".join("%s %s" % (type_to_cs(arg.type), arg.name) for arg in method.args)
                with BLOCK("public {0} {1}({2})", type_to_cs(method.type), method.name, args):
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

    def generate_client(self, module, service):
        BLOCK = module.block
        STMT = module.stmt
        SEP = module.sep















