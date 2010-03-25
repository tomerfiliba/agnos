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
#    else:
#        if isinstance(t, compiler.Object):
#            if proxy:
#                return "%sProxy" % (t.name,)
#            if ref:
#                return type_to_java(compiler.ObjRef)
#            if interface:
#                return "I%s" % (t.name,)
#        return t.name

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
    return "%s$packer" % (t,)


class JavaTarget(TargetBase):
    @contextmanager
    def new_module(self, filename):
        mod = blocklang.Module()
        yield mod
        with self.open(filename) as f:
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
                    if isinstance(member, compiler.Exception):
                        self.generate_exception(module, member)

                for member in service.types.values():
                    if isinstance(member, compiler.Class):
                        self.generate_class_interface(module, member)
                        self.generate_class_proxy(module, member)
    
    def generate_enum(self, module, enum):
        BLOCK = module.block
        STMT = module.stmt
        SEP = module.sep
        with BLOCK("public enum {0}", enum.name):
            for mem in enum.members[:-1]:
                STMT("{0} = {1},", mem.name, mem.value, colon = False)
            STMT("{0} = {1}", enum.members[-1].name, enum.members[-1].value, colon = False)
        SEP()
    
    def generate_record(self, module, rec):
        BLOCK = module.block
        STMT = module.stmt
        SEP = module.sep
        with BLOCK("public static class {0}", rec.name):
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
        with BLOCK("protected static class _{0}Record implements IPacker", rec.name):
            with BLOCK("public void pack(Object obj, OutputStream stream) throws IOException"):
                STMT("{0} val = ({0})obj", rec.name)
                for mem in rec.members:
                    STMT("{0}.pack(val.{1}, stream)", type_to_packer(mem.type), mem.name)

            with BLOCK("public Object unpack(InputStream stream) throws IOException"):
                args = ", ".join("(%s)%s.unpack(stream)" % (type_to_java(mem.type), type_to_packer(mem.type)) for mem in rec.members)
                STMT("return new {0}({1})", rec.name, args)
        SEP()
        STMT("protected static _{0}Record {0}Record = new _{0}Record()", rec.name)
        SEP()

    def generate_exception(self, module, rec):
        BLOCK = module.block
        STMT = module.stmt
        SEP = module.sep
        with BLOCK("public static class {0} extends Exception", rec.name):
            for mem in rec.members:
                STMT("public {0} {1}", type_to_java(mem.type), mem.name)
            SEP()
            with BLOCK("public {0}()", rec.name):
                pass
            args = ", ".join("%s %s" % (type_to_java(mem.type), mem.name) for mem in rec.members)
            with BLOCK("public {0}({1})", rec.name, args):
                for mem in rec.members:
                    STMT("this.{0} = {0}", mem.name)
            with BLOCK("public String toString()"):
                args = " + ".join(mem.name for mem in rec.members)
                STMT('return "{0}(" + {1} + ")"', rec.name, args)
        SEP()
        with BLOCK("protected static class _{0}Record implements IPacker", rec.name):
            with BLOCK("public void pack(Object obj, OutputStream stream) throws IOException"):
                STMT("{0} val = ({0})obj", rec.name)
                for mem in rec.members:
                    STMT("{0}.pack(val.{1}, stream)", type_to_packer(mem.type), mem.name)

            with BLOCK("public Object unpack(InputStream stream) throws IOException"):
                args = ", ".join("(%s)%s.unpack(stream)" % (type_to_java(mem.type), type_to_packer(mem.type)) for mem in rec.members)
                STMT("return new {0}({1})", rec.name, args)
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
                    STMT("{0} get_{1}()", type_to_java(attr.type), attr.name)
                if attr.set:
                    STMT("void set_{1}({0} value)", attr.name, type_to_java(attr.type))
            SEP()
            if cls.attrs:
                DOC("methods")
            for method in cls.methods:
                args = ", ".join("%s %s" % (type_to_java(arg.type), arg.name) for arg in method.args)
                STMT("{0} {1}({2})", type_to_java(method.type), method.name, args)
        SEP()

    def generate_class_proxy(self, module, cls):
        BLOCK = module.block
        STMT = module.stmt
        SEP = module.sep
        DOC = module.doc
        with BLOCK("public static class {0}Proxy implements I{0}", cls.name):
            STMT("protected Object __client")
            STMT("protected {0} __objref", type_to_java(compiler.t_objref))
            STMT("protected boolean __disposed")
            SEP()
            with BLOCK("protected {0}Proxy(Object client, {1} objref)", cls.name, type_to_java(compiler.t_objref)):
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
                    STMT("_client._decref(__objref)", cls.name)
            SEP()
            for attr in cls.attrs:
                if attr.get:
                    with BLOCK("public {0} get_{1}()", type_to_java(attr.type), attr.name):
                        STMT("return __client._{0}_get_{1}(__objref)", cls.name, attr.name)
                if attr.set:
                    with BLOCK("public void set_{1}({0} value)", attr.name, type_to_java(attr.type)):
                        STMT("__client._{0}_set_{1}(__objref, value)", cls.name, attr.name)
            
            for method in cls.methods:
                args = ", ".join("%s %s" % (type_to_java(arg.type), arg.name) for arg in method.args)
                with BLOCK("public {0} {1}({2})", type_to_java(method.type), method.name, args):
                    callargs = ["__objref"] + [arg.name for arg in method.args]
                    STMT("__client._{0}_{1}({2})", cls.name, attr.name, ", ".join(callargs))
        SEP()


    def generate_service(self, service):
        with self.new_module("%s.java" % (service.name,)) as module:
            BLOCK = module.block
            STMT = module.stmt
            SEP = module.sep
            
            STMT("package {0}", service.name)
            SEP()
            STMT("import java.util.*")
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
            with BLOCK("public Processor(IHandler handler, InputStream inStream, OutputStream outStream)"):
                STMT("super(inStream, outStream)")
                STMT("this.handler = handler")
            SEP()
            with BLOCK("protected void process_invoke(int seq)"):
                STMT("int funcid = {0}.unpack(inStream)", type_to_packer(compiler.t_int32))
                STMT("IPacker packer = null")
                STMT("Object result = null")
                with BLOCK("try"):
                    with BLOCK("switch (funcid)"):
                        with BLOCK("case 1:", prefix = None, suffix = None):
                            STMT("Long id = (Long)(Packers.Int64.unpack(inStream))")
                            STMT("decref(id)")
                        for func in funcs:
                            with BLOCK("case {0}:", func.funcid, prefix = None, suffix = None):
                                if isinstance(func, compiler.Func):
                                    args = ", ".join("(%s)(%s.unpack(inStream))" % (type_to_java(arg.type), type_to_packer(arg.type)) for arg in func.args)
                                    STMT("result = handler.{1}({2})", type_to_java(func.type), func.name, args)
                                else:
                                    STMT("Long id = (Long)(Packers.Int64.unpack(inStream))")
                                    args = ", ".join("(%s)(%s.unpack(inStream))" % (type_to_java(arg.type), type_to_packer(arg.type)) for arg in func.args[1:])
                                    STMT("result = (({0})load(id)).{1}({2})", type_to_java(func.origin.parent), func.origin.name, args)
                                if isinstance(func.type, compiler.Class):
                                    STMT("result = store(result)")
                                STMT("packer = {0}", type_to_packer(func.type))
                                STMT("break")
                        with BLOCK("default:", prefix = None, suffix = None):
                            STMT("throw new ProtocolError()")
                with BLOCK("catch (Exception ex)"):
                    STMT("{0}.pack(new Integer(seq), outStream)", type_to_packer(compiler.t_int32))
                    STMT("{0}.pack(new Byte((byte)REPLY_EXECUTION_ERROR), outStream)", type_to_packer(compiler.t_int8))
                    STMT("return")
                SEP()
                STMT("{0}.pack(new Integer(seq), outStream)", type_to_packer(compiler.t_int32))
                STMT("{0}.pack(new Byte((byte)REPLY_SUCCESS), outStream)", type_to_packer(compiler.t_int8))
                with BLOCK("if (packer != null)"):
                    STMT("packer.pack(result, outStream)")
        SEP()
    
    def generate_client(self, module, service):
        BLOCK = module.block
        STMT = module.stmt
        SEP = module.sep
        DOC = module.doc
        with BLOCK("public static class Client extends Protocol.BaseClient"):
            with BLOCK("public Client(InputStream inStream, OutputStream, outStream)"):
                STMT("super(inStream, outStream)")
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
                with BLOCK("{0} {1} {2}({3})", access, type_to_java(func.type, proxy = True), func.name, args):
                    STMT("_cmd_invoke({0})", func.funcid)
                    for arg in func.args:
                        STMT("{0}.pack({1}, _outStream)", type_to_packer(arg.type), arg.name)
                    STMT("_outStream.flush()")
                    STMT("Object res = _read_result({0})", type_to_packer(func.type))
                    if isinstance(func.type, compiler.Class):
                        STMT("return new {0}(this, (Long)res)", type_to_java(func.type, proxy = True))
                    else:
                        STMT("return ({0})res", type_to_java(func.type))
        SEP()











