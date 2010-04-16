from contextlib import contextmanager
from .base import TargetBase
from . import blocklang
from .. import compiler


def type_to_cs(t, proxy = False):
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
        return "List<%s>" % (type_to_cs(t.oftype, proxy = proxy),)
    elif isinstance(t, compiler.TMap):
        return "Map<%s, %s>" % (
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
        return "Types.%sRecord" % (t.name,)
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
        mod = blocklang.Module()
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
                for member in service.consts.values():
                    STMT("public static const {0} {1} = {2}", type_to_cs(member.type), member.name, const_to_cs(member.type, member.value))
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





