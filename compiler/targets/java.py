from contextlib import contextmanager
from .base import TargetBase
from . import blocklang
from .. import compiler


def type_to_java(t, proxy = False, ref = False, interface = False):
    if t == compiler.t_void:
        return "void"
    elif t == compiler.t_bool:
        return "Boolean"
    elif t == compiler.t_int8:
        return "Byte"
    elif t == compiler.t_int16:
        return "Short"
    elif t == compiler.t_int32:
        return "Integer"
    elif t == compiler.t_int64:
        return "Long"
    elif t == compiler.t_float:
        return "Double"
    elif t == compiler.t_string:
        return "String"
    elif t == compiler.t_date:
        return "Date"
    elif t == compiler.t_buffer:
        return "byte[]"
    elif t == compiler.t_objref:
        return "Long" 
    elif isinstance(t, compiler.TList):
        return "List<%s>" % (type_to_java(t.oftype, proxy = proxy, ref = ref, interface = interface),)
    elif isinstance(t, compiler.TMap):
        return "Map<%s, %s>" % (
            type_to_java(t.keytype, proxy = proxy, ref = ref, interface = interface), 
            type_to_java(t.valtype, proxy = proxy, ref = ref, interface = interface))
    elif isinstance(t, (compiler.Enum, compiler.Record, compiler.Exception)):
        return "Types.%s" % (t.name,)
    elif isinstance(t, compiler.Class):
        if proxy:
            return "Types.%sProxy" % (t.name,)
        else:
            return "Types.I%s" % (t.name,)
    else:
        return "%s$type" % (t,)

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
        return "Types.%sRecord" % (t.name,)
    if isinstance(t, compiler.Enum):
        return type_to_packer(compiler.t_int32)
    if isinstance(t, compiler.Class):
        return type_to_packer(compiler.t_objref)
    return "%s$packer" % (t,)


class JavaTarget(TargetBase):
    @contextmanager
    def new_module(self, filename):
        mod = blocklang.Module()
        yield mod
        with self.open(filename, "w") as f:
            f.write(mod.render())

    def generate(self, service):
        self.generate_types(service)
        self.generate_service(service)
    
    def generate_types(self, service):
        with self.new_module("Types.java") as module:
            BLOCK = module.block
            STMT = module.stmt
            SEP = module.sep
            
            STMT("package {0}", service.name)
            SEP()
            STMT("import java.util.*")
            STMT("import java.io.*")
            STMT("import agnos.*")
            SEP()
            with BLOCK("public class Types"):
                for member in service.types.values():
                    if isinstance(member, compiler.Enum):
                        self.generate_enum(module, member)
                
                for member in service.types.values():
                    if isinstance(member, compiler.Record):
                        self.generate_record(module, member)

                for member in service.types.values():
                    if isinstance(member, compiler.Class):
                        self.generate_class_interface(module, member)
                        self.generate_class_proxy(module, service, member)
    
    def generate_enum(self, module, enum):
        BLOCK = module.block
        STMT = module.stmt
        SEP = module.sep
        with BLOCK("public enum {0}", enum.name):
            for mem in enum.members[:-1]:
                STMT("{0} ({1}),", mem.name, mem.value, colon = False)
            STMT("{0} ({1})", enum.members[-1].name, enum.members[-1].value)
            SEP()
            STMT("public Integer value")
            with BLOCK("private static final Map<Integer, {0}> BY_VALUE = new HashMap<Integer,{0}>()", enum.name, prefix = "{{", suffix = "}};"):
                with BLOCK("for({0} member : {0}.values())", enum.name):
                    STMT("put(member.value, member)")
            SEP()
            with BLOCK("private {0}(int v)", enum.name):
                STMT("value = new Integer(v)")
            with BLOCK("public static {0} getByValue(Integer v)", enum.name):
                STMT("return BY_VALUE.get(v)")
        SEP()
    
    def generate_record(self, module, rec):
        BLOCK = module.block
        STMT = module.stmt
        SEP = module.sep
        if isinstance(rec, compiler.Exception):
            isexc = True
            extends = "extends Protocol.PackedException"
        else:
            isexc = False
            extends = ""
        with BLOCK("public static class {0} {1}", rec.name, extends):
            STMT("protected final static Integer __record_id = new Integer({0})", rec.id)
            for mem in rec.members:
                STMT("public {0} {1}", type_to_java(mem.type), mem.name)
            SEP()
            with BLOCK("public {0}()", rec.name):
                pass
            args = ", ".join("%s %s" % (type_to_java(mem.type), mem.name) for mem in rec.members)
            with BLOCK("public {0}({1})", rec.name, args):
                for mem in rec.members:
                    STMT("this.{0} = {0}", mem.name)
            with BLOCK("public void pack(OutputStream stream) throws IOException"):
                STMT("Packers.Int32.pack(__record_id, stream)")
                STMT("{0}Record.pack(this, stream)", rec.name)
        SEP()
        with BLOCK("protected static class _{0}Record implements Packers.IPacker", rec.name):
            with BLOCK("public void pack(Object obj, OutputStream stream) throws IOException"):
                STMT("{0} val = ({0})obj", rec.name)
                for mem in rec.members:
                    if isinstance(mem.type, compiler.Enum):
                        STMT("Packers.Int32.pack(val.{0}.value, stream)", mem.name)
                    else:
                        STMT("{0}.pack(val.{1}, stream)", type_to_packer(mem.type), mem.name)

            with BLOCK("public Object unpack(InputStream stream) throws IOException"):
                args = []
                for mem in rec.members:
                    if isinstance(mem, compiler.Enum):
                        args.append("%s.getByValue((Integer)Packers.Int32.unpack(stream))" % (type_to_java(mem.type), type_to_packer(mem.type)))
                    else:
                        args.append("(%s)%s.unpack(stream)" % (type_to_java(mem.type), type_to_packer(mem.type)))
                STMT("return new {0}({1})", rec.name, ", ".join(args))
        SEP()
        STMT("protected static _{0}Record {0}Record = new _{0}Record()", rec.name)
        SEP()

    def generate_class_interface(self, module, cls):
        BLOCK = module.block
        STMT = module.stmt
        SEP = module.sep
        DOC = module.doc
        with BLOCK("public interface I{0}", cls.name):
            if cls.attrs:
                DOC("attributes")
            for attr in cls.attrs:
                if attr.get:
                    STMT("{0} get_{1}() throws IOException, Protocol.ProtocolError, Protocol.PackedException", type_to_java(attr.type), attr.name)
                if attr.set:
                    STMT("void set_{1}({0} value) throws IOException, Protocol.ProtocolError, Protocol.PackedException", attr.name, type_to_java(attr.type))
            SEP()
            if cls.attrs:
                DOC("methods")
            for method in cls.methods:
                args = ", ".join("%s %s" % (type_to_java(arg.type), arg.name) for arg in method.args)
                STMT("{0} {1}({2}) throws IOException, Protocol.ProtocolError, Protocol.PackedException", type_to_java(method.type), method.name, args)
        SEP()

    def generate_class_proxy(self, module, service, cls):
        BLOCK = module.block
        STMT = module.stmt
        SEP = module.sep
        DOC = module.doc
        with BLOCK("public static class {0}Proxy implements I{0}", cls.name):
            STMT("protected {0}.Client __client", service.name)
            STMT("protected Long __objref")
            STMT("protected boolean __disposed")
            SEP()
            with BLOCK("protected {0}Proxy({1}.Client client, Long objref)", cls.name, service.name):
                STMT("__client = client")
                STMT("__objref = objref")
                STMT("__disposed = false")
            SEP()
            with BLOCK("public void finalize()"):
                STMT("dispose()")
            with BLOCK("public void dispose()"):
                with BLOCK("if (__disposed)"):
                    STMT("return")
                with BLOCK("synchronized(this)"):
                    STMT("__disposed = true")
                    STMT("__client._decref(__objref)", cls.name)
            SEP()
            for attr in cls.attrs:
                if attr.get:
                    with BLOCK("public {0} get_{1}() throws IOException, Protocol.ProtocolError, Protocol.PackedException", type_to_java(attr.type), attr.name):
                        STMT("return __client._{0}_get_{1}(__objref)", cls.name, attr.name)
                if attr.set:
                    with BLOCK("public void set_{1}({0} value) throws IOException, Protocol.ProtocolError, Protocol.PackedException", attr.name, type_to_java(attr.type)):
                        STMT("__client._{0}_set_{1}(__objref, value)", cls.name, attr.name)
            
            for method in cls.methods:
                args = ", ".join("%s %s" % (type_to_java(arg.type), arg.name) for arg in method.args)
                with BLOCK("public {0} {1}({2}) throws IOException, Protocol.ProtocolError, Protocol.PackedException", type_to_java(method.type), method.name, args):
                    callargs = ["__objref"] + [arg.name for arg in method.args]
                    if method.type == compiler.t_void:
                        STMT("__client._{0}_{1}({2})", cls.name, method.name, ", ".join(callargs))
                    else:
                        STMT("return __client._{0}_{1}({2})", cls.name, method.name, ", ".join(callargs))
        SEP()

    def generate_service(self, service):
        with self.new_module("%s.java" % (service.name,)) as module:
            BLOCK = module.block
            STMT = module.stmt
            SEP = module.sep
            
            STMT("package {0}", service.name)
            SEP()
            STMT("import java.util.*")
            STMT("import java.io.*")
            STMT("import agnos.*")
            SEP()
            with BLOCK("public class {0}", service.name):
                self.generate_handler_interface(module, service)
                self.generate_processor(module, service)
                self.generate_client(module, service)

    def generate_handler_interface(self, module, service):
        BLOCK = module.block
        STMT = module.stmt
        SEP = module.sep
        with BLOCK("public interface IHandler"):
            for member in service.roots.values():
                if isinstance(member, compiler.Func):
                    args = ", ".join("%s %s" % (type_to_java(arg.type), arg.name) for arg in member.args)
                    STMT("{0} {1}({2})", type_to_java(member.type), member.name, args)
        SEP()

    def generate_processor(self, module, service):
        BLOCK = module.block
        STMT = module.stmt
        SEP = module.sep
        funcs = [mem for mem in service.roots.values()
            if isinstance(mem, (compiler.Func, compiler.AutoGeneratedFunc))]

        with BLOCK("public static class Processor extends Protocol.BaseProcessor"):
            STMT("protected IHandler handler")
            SEP()
            with BLOCK("public Processor(IHandler handler)"):
                STMT("super()")
                STMT("this.handler = handler")
            SEP()
            with BLOCK("protected void process_invoke(InputStream inStream, OutputStream outStream, int seq) throws IOException, Protocol.ProtocolError, Protocol.PackedException"):
                STMT("int funcid = (Integer){0}.unpack(inStream)", type_to_packer(compiler.t_int32))
                STMT("Packers.IPacker packer = null")
                STMT("Object result = null")
                STMT("Long id")
                with BLOCK("switch (funcid)"):
                    for func in funcs:
                        with BLOCK("case {0}:", func.id, prefix = None, suffix = None):
                            if isinstance(func, compiler.Func):
                                args = []
                                for arg in func.args:
                                    if isinstance(arg.type, compiler.Class):
                                        args.append("(%s)(load((Long)Packers.Int64.unpack(inStream)))" % (type_to_java(arg.type)))
                                    else:
                                        args.append("(%s)(%s.unpack(inStream))" % (type_to_java(arg.type), type_to_packer(arg.type)))
                                if func.type == compiler.t_void:
                                    STMT("handler.{0}({1})", type_to_java(func.type), func.name, ", ".join(args))
                                else:
                                    STMT("result = handler.{0}({1})", func.name, ", ".join(args))
                            else:
                                args = []
                                for arg in func.args[1:]:
                                    if isinstance(arg.type, compiler.Class):
                                        args.append("(%s)(load((Long)Packers.Int64.unpack(inStream)))" % (type_to_java(arg.type)))
                                    else:
                                        args.append("(%s)(%s.unpack(inStream))" % (type_to_java(arg.type), type_to_packer(arg.type)))
                                STMT("id = (Long)(Packers.Int64.unpack(inStream))")
                                if isinstance(func.origin, compiler.ClassAttr):
                                    if "_get_" in func.name:
                                        STMT("result = (({0})load(id)).get_{1}({2})", type_to_java(func.origin.parent), func.origin.name, ", ".join(args))
                                    else:
                                        STMT("(({0})load(id)).set_{1}({2})", type_to_java(func.origin.parent), func.origin.name, ", ".join(args))
                                else:
                                    if func.type == compiler.t_void:
                                        STMT("(({0})load(id)).{1}({2})", type_to_java(func.origin.parent), func.origin.name, ", ".join(args))
                                    else:
                                        STMT("result = (({0})load(id)).{1}({2})", type_to_java(func.origin.parent), func.origin.name, ", ".join(args))
                            if isinstance(func.type, compiler.Class):
                                STMT("result = store(result)")
                            STMT("packer = {0}", type_to_packer(func.type))
                            STMT("break")
                    with BLOCK("default:", prefix = None, suffix = None):
                        STMT('throw new Protocol.ProtocolError("unknown function id: " + funcid)')
                SEP()
                STMT("{0}.pack(new Integer(seq), outStream)", type_to_packer(compiler.t_int32))
                STMT("{0}.pack(new Byte((byte)Protocol.REPLY_SUCCESS), outStream)", type_to_packer(compiler.t_int8))
                with BLOCK("if (packer != null)"):
                    STMT("packer.pack(result, outStream)")
                STMT("outStream.flush()")
        SEP()
    
    def generate_client(self, module, service):
        BLOCK = module.block
        STMT = module.stmt
        SEP = module.sep
        DOC = module.doc
        with BLOCK("public static class Client extends Protocol.BaseClient"):
            with BLOCK("public Client(InputStream inStream, OutputStream outStream)"):
                STMT("super(inStream, outStream)")
            SEP()
            with BLOCK("protected void _decref(Long id)"):
                STMT("super._decref(id)")
            SEP()
            with BLOCK("protected Protocol.PackedException _load_packed_exception() throws IOException, Protocol.ProtocolError"):
                STMT("int clsid = (Integer)Packers.Int32.unpack(_inStream)")
                with BLOCK("switch (clsid)"):
                    for mem in service.types:
                        if not isinstance(mem, compiler.Exception):
                            continue
                        with BLOCK("case {0}:", mem.id, prefix = None, suffix = None):
                            STMT("return (Protocol.PackedException)(Types.{0}Record.unpack(_outStream))")
                    with BLOCK("default:", prefix = None, suffix = None):
                        STMT('throw new Protocol.ProtocolError("unknown exception class id: " + clsid)')
            SEP()
            for mem in service.roots.values():
                if isinstance(mem, compiler.Func):
                    access = "public"
                elif isinstance(mem, compiler.AutoGeneratedFunc):
                    access = "protected"
                else:
                    continue
                func = mem
                args = ", ".join("%s %s" % (type_to_java(arg.type, proxy = True), arg.name) for arg in func.args)
                with BLOCK("{0} {1} {2}({3}) throws IOException, Protocol.ProtocolError, Protocol.PackedException", access, type_to_java(func.type, proxy = True), func.name, args):
                    STMT("_cmd_invoke({0})", func.id)
                    for arg in func.args:
                        if isinstance(arg.type, compiler.Class):
                            STMT("Packers.Int64.pack({0}.__objref, _outStream)", arg.name)
                        else:
                            STMT("{0}.pack({1}, _outStream)", type_to_packer(arg.type), arg.name)
                    STMT("_outStream.flush()")
                    STMT("Object res = _read_reply({0})", type_to_packer(func.type))
                    if isinstance(func.type, compiler.Class):
                        STMT("return new {0}(this, (Long)res)", type_to_java(func.type, proxy = True))
                    elif func.type != compiler.t_void:
                        STMT("return ({0})res", type_to_java(func.type))
        SEP()











