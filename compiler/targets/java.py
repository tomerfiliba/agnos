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
        return t.name
    else:
        return "$%s$" % (t,)
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
    if t == compiler.t_bool:
        return "Datatypes.Bool"
    if t == compiler.t_int8:
        return "Datatypes.Int8"
    if t == compiler.t_int16:
        return "Datatypes.Int16"
    if t == compiler.t_int32:
        return "Datatypes.Int32"
    if t == compiler.t_int64:
        return "Datatypes.Int64"
    if t == compiler.t_float:
        return "Datatypes.Float"
    if t == compiler.t_date:
        return "Datatypes.Date"
    if t == compiler.t_buffer:
        return "Datatypes.Buffer"
    if t == compiler.t_string:
        return "Datatypes.Str"
    if isinstance(t, (compiler.Record, compiler.Exception)):
        return "%sRecord" % (t.name,)
    if isinstance(t, compiler.Enum):
        return type_to_packer(compiler.t_int32)
    return "^%s^" % (t,)


class JavaTarget(TargetBase):
    @contextmanager
    def new_module(self, filename):
        mod = blocklang.Module()
        yield mod
        with self.open(filename) as f:
            f.write(mod.render())

    def generate(self, service):
        self.generate_types(service)
    
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
        with BLOCK("public static class _{0}Record implements IDatatype", rec.name):
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
        with BLOCK("public static class _{0}Record implements IDatatype", rec.name):
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
        pass

    def generate_class_proxy(self, module, cls):
        pass































