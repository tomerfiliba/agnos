from contextlib import contextmanager
from .base import TargetBase
from ..langs import clike
from .. import compiler


def type_to_java(t, proxy = False):
    if t == compiler.t_void:
        return "void"
    elif t == compiler.t_bool:
        return "boolean"
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
        return "date"
    elif t == compiler.t_buffer:
        return "byte[]"
    elif t == compiler.t_objref:
        return "Long" 
    elif isinstance(t, compiler.TList):
        return "List<%s>" % (type_to_java(t.oftype, proxy = proxy),)
    elif isinstance(t, compiler.TMap):
        return "Map<%s, %s>" % (
            type_to_java(t.keytype, proxy = proxy), 
            type_to_java(t.valtype, proxy = proxy))
    elif isinstance(t, (compiler.Enum, compiler.Record, compiler.Exception)):
        return "%s" % (t.name,)
    elif isinstance(t, compiler.Class):
        if proxy:
            return "%sProxy" % (t.name,)
        else:
            return "I%s" % (t.name,)
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
        return "%sRecord" % (t.name,)
    if isinstance(t, compiler.Enum):
        return type_to_packer(compiler.t_int32)
    if isinstance(t, compiler.Class):
        return type_to_packer(compiler.t_objref)
    return "%r$packer" % (t,)

def const_to_java(typ, val):
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
        raise IDLError("%r cannot be converted to a java const" % (val,))


class JavaTarget(TargetBase):
    DEFAULT_TARGET_DIR = "gen-java"
    
    @contextmanager
    def new_module(self, filename):
        mod = clike.Module()
        yield mod
        with self.open(filename, "w") as f:
            f.write(mod.render())

    def generate(self, service):
        with self.new_module("%s.java" % (service.name,)) as module:
            BLOCK = module.block
            STMT = module.stmt
            SEP = module.sep
            DOC = module.doc
            
            STMT("package {0}", service.name)
            SEP()
            STMT("import java.util.*")
            STMT("import java.io.*")
            STMT("import agnos.*")
            SEP()
            with BLOCK("public class {0}", service.name):
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
                    STMT("public final static {0} {1} = {2}", type_to_java(member.type), member.name, const_to_java(member.type, member.value))
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
                STMT("{0} ({1}),", mem.name, mem.value, colon = False)
            STMT("{0} ({1})", enum.members[-1].name, enum.members[-1].value)
            SEP()
            STMT("public Integer value")
            with BLOCK("private static final Map<Integer, {0}> _BY_VALUE = new HashMap<Integer, {0}>()", enum.name, prefix = "{{", suffix = "}};"):
                with BLOCK("for({0} member : {0}.values())", enum.name):
                    STMT("put(member.value, member)")
            with BLOCK("private static final Map<String, {0}> _BY_NAME = new HashMap<String, {0}>()", enum.name, prefix = "{{", suffix = "}};"):
                with BLOCK("for({0} member : {0}.values())", enum.name):
                    STMT("put(member.toString(), member)")
            SEP()
            with BLOCK("private {0}(int v)", enum.name):
                STMT("value = new Integer(v)")
            with BLOCK("public static {0} getByValue(Integer val)", enum.name):
                STMT("return _BY_VALUE.get(val)")
            with BLOCK("public static {0} getByName(String name)", enum.name):
                STMT("return _BY_NAME.get(name)")
    
    def generate_record(self, module, rec):
        BLOCK = module.block
        STMT = module.stmt
        SEP = module.sep
        if isinstance(rec, compiler.Exception):
            extends = "extends Protocol.PackedException"
        else:
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
            SEP()
            with BLOCK("public void pack(OutputStream stream) throws IOException"):
                STMT("Packers.Int32.pack(__record_id, stream)")
                STMT("{0}Record.pack(this, stream)", rec.name)
            SEP()
            with BLOCK("public String toString()"):
                STMT('return "{0}(" + {1} + ")"', rec.name, ' + ", " + '.join(mem.name  for mem in rec.members))
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
                    if isinstance(mem.type, compiler.Enum):
                        args.append("%s.getByValue((Integer)Packers.Int32.unpack(stream))" % (type_to_java(mem.type),))
                    else:
                        args.append("(%s)%s.unpack(stream)" % (type_to_java(mem.type), type_to_packer(mem.type)))
                STMT("return new {0}({1})", rec.name, ", ".join(args))
        SEP()
        STMT("protected static _{0}Record {0}Record = new _{0}Record()", rec.name)

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
                    STMT("{0} get_{1}() throws Exception", type_to_java(attr.type), attr.name)
                if attr.set:
                    STMT("void set_{1}({0} value) throws Exception", attr.name, type_to_java(attr.type))
            SEP()
            if cls.methods:
                DOC("methods")
            for method in cls.methods:
                args = ", ".join("%s %s" % (type_to_java(arg.type), arg.name) for arg in method.args)
                STMT("{0} {1}({2}) throws Exception", type_to_java(method.type), method.name, args)

    def generate_base_class_proxy(self, module, service):
        BLOCK = module.block
        STMT = module.stmt
        SEP = module.sep
        DOC = module.doc
        with BLOCK("public static abstract class BaseProxy"):
            STMT("protected Long _objref")
            STMT("protected Client _client")
            STMT("protected boolean _disposed")
            SEP()
            with BLOCK("protected BaseProxy(Client client, Long objref)"):
                STMT("_client = client")
                STMT("_objref = objref")
                STMT("_disposed = false")
            SEP()
            with BLOCK("public void finalize()"):
                STMT("dispose()")
            SEP()
            with BLOCK("public void dispose()"):
                with BLOCK("if (_disposed)"):
                    STMT("return")
                with BLOCK("synchronized (this)"):
                    STMT("_disposed = true")
                    STMT("_client._decref(_objref)")
            SEP()
            with BLOCK("public String toString()"):
                STMT('return super.toString() + "<" + _objref + ">"')

    def emit_javadoc(self, text, module):
        if isinstance(text, basestring):
            text = [text]
        text = "\n".join(text)
        text = text.strip()
        if not text:
            return
        module.stmt("/**", colon = False)
        for line in text.splitlines():
            module.stmt(" * {0}", line.strip(), colon = False)
        module.stmt(" */", colon = False)

    def emit_func_javadoc(self, func, module):
        chunks = [func.doc]
        if func.doc:
            chunks.append("")
        for arg in func.args:
            chunks.append(" @param %s     %s" % (arg.name, arg.doc)) 
        self.emit_javadoc(chunks, module)
    
    def generate_class_proxy(self, module, service, cls):
        BLOCK = module.block
        STMT = module.stmt
        SEP = module.sep
        DOC = module.doc
        with BLOCK("public static class {0}Proxy extends BaseProxy", cls.name):
            with BLOCK("protected {0}Proxy(Client client, Long objref)", cls.name):
                STMT("super(client, objref)")
            SEP()
            for attr in cls.attrs:
                if attr.get:
                    self.emit_javadoc(["Getter for %s" % (attr.name,), attr.doc], module)
                    with BLOCK("public {0} get_{1}() throws Exception", type_to_java(attr.type), attr.name):
                        STMT("return _client._{0}_get_{1}(this)", cls.name, attr.name)
                if attr.set:
                    self.emit_javadoc(["Setter for %s" % (attr.name,), attr.doc], module)
                    with BLOCK("public void set_{1}({0} value) throws Exception", attr.name, type_to_java(attr.type)):
                        STMT("_client._{0}_set_{1}(this, value)", cls.name, attr.name)
            SEP()
            for method in cls.methods:
                self.emit_func_javadoc(method, module)
                args = ", ".join("%s %s" % (type_to_java(arg.type, proxy = True), arg.name) for arg in method.args)
                with BLOCK("public {0} {1}({2}) throws Exception", type_to_java(method.type), method.name, args):
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
                    args = ", ".join("%s %s" % (type_to_java(arg.type), arg.name) for arg in member.args)
                    STMT("{0} {1}({2}) throws Exception", type_to_java(member.type), member.name, args)

    def generate_processor(self, module, service):
        BLOCK = module.block
        STMT = module.stmt
        SEP = module.sep
        funcs = [mem for mem in service.funcs.values()
            if isinstance(mem, (compiler.Func, compiler.AutoGeneratedFunc))]

        with BLOCK("public static class Processor extends Protocol.BaseProcessor"):
            STMT("protected IHandler handler")
            SEP()
            with BLOCK("public Processor(IHandler handler)"):
                STMT("super()")
                STMT("this.handler = handler")
            SEP()
            with BLOCK("protected void process_invoke(InputStream inStream, OutputStream outStream, int seq) throws Exception"):
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
                                    STMT("handler.{0}({1})", func.name, ", ".join(args))
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
                                #elif func.origin == func.origin.parent:
                                #    STMT("result = new (({0})load(id)).{1}({2})", type_to_java(func.origin.parent), func.origin.name, ", ".join(args))
                                else:
                                    if func.type == compiler.t_void:
                                        STMT("(({0})load(id)).{1}({2})", type_to_java(func.origin.parent), func.origin.name, ", ".join(args))
                                    else:
                                        STMT("result = (({0})load(id)).{1}({2})", type_to_java(func.origin.parent), func.origin.name, ", ".join(args))
                            if isinstance(func.type, compiler.Class):
                                STMT("result = store(result)")
                            if func.type != compiler.t_void:
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
    
    def generate_client(self, module, service):
        BLOCK = module.block
        STMT = module.stmt
        SEP = module.sep
        DOC = module.doc
        with BLOCK("public static class Client extends Protocol.BaseClient"):
            with BLOCK("public Client(InputStream inStream, OutputStream outStream)"):
                STMT("super(inStream, outStream)")
            with BLOCK("public Client(Transports.ITransport transport) throws IOException"):
                STMT("super(transport)")
            SEP()
            with BLOCK("protected void _decref(Long id)"):
                # to avoid protectedness issues
                STMT("super._decref(id)")
            SEP()
            with BLOCK("protected Protocol.PackedException _load_packed_exception() throws IOException, Protocol.ProtocolError"):
                STMT("int clsid = (Integer)Packers.Int32.unpack(_inStream)")
                with BLOCK("switch (clsid)"):
                    for mem in service.types.values():
                        if not isinstance(mem, compiler.Exception):
                            continue
                        with BLOCK("case {0}:", mem.id, prefix = None, suffix = None):
                            STMT("return (Protocol.PackedException)({0}Record.unpack(_inStream))", mem.name)
                    with BLOCK("default:", prefix = None, suffix = None):
                        STMT('throw new Protocol.ProtocolError("unknown exception class id: " + clsid)')
            SEP()
            for func in service.funcs.values():
                if isinstance(func, compiler.Func):
                    access = "public"
                    self.emit_func_javadoc(func, module)
                elif isinstance(func, compiler.AutoGeneratedFunc):
                    access = "protected"
                else:
                    continue
                args = ", ".join("%s %s" % (type_to_java(arg.type, proxy = True), arg.name) for arg in func.args)
                with BLOCK("{0} {1} {2}({3}) throws IOException, Protocol.ProtocolError, Protocol.PackedException, Protocol.GenericError", access, type_to_java(func.type, proxy = True), func.name, args):
                    STMT("_cmd_invoke({0})", func.id)
                    for arg in func.args:
                        if isinstance(arg.type, compiler.Class):
                            STMT("Packers.Int64.pack({0}._objref, _outStream)", arg.name)
                        else:
                            STMT("{0}.pack({1}, _outStream)", type_to_packer(arg.type), arg.name)
                    STMT("_outStream.flush()")
                    STMT("Object res = _read_reply({0})", type_to_packer(func.type))
                    if isinstance(func.type, compiler.Class):
                        STMT("return new {0}(this, (Long)res)", type_to_java(func.type, proxy = True))
                    elif func.type != compiler.t_void:
                        STMT("return ({0})res", type_to_java(func.type))











