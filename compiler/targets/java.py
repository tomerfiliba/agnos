import itertools
from contextlib import contextmanager
from .base import TargetBase, is_complex_type, NOOP
from ..langs import clike
from .. import compiler


def type_to_java(t, proxy = False):
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
    elif t == compiler.t_heteromap:
        return "agnos.HeteroMap"
    elif isinstance(t, compiler.TList):
        #return "%s[]" % (type_to_java(t.oftype, proxy = proxy),)
        return "List<%s>" % (type_to_java(t.oftype, proxy = False),)
    elif isinstance(t, compiler.TMap):
        return "Map<%s, %s>" % (type_to_java(t.keytype, proxy = False), 
            type_to_java(t.valtype, proxy = False))
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

def const_to_java(typ, val):
    if val is None:
        return "null"
    elif typ == compiler.t_bool:
        if val:
            return "true"
        else:
            return "false"
    elif typ == compiler.t_int8:
        return "new Byte(%r)" % (val,)
    elif typ == compiler.t_int16:
        return "new Short(%r)" % (val,)
    elif typ == compiler.t_int32:
        return "new Integer(%r)" % (val,)
    elif typ == compiler.t_int64:
        return "new Long(%r)" % (val,)
    elif typ == compiler.t_float:
        return "new Double(%r)" % (val,)
    elif typ == compiler.t_string:
        return repr(val)
    #elif isinstance(val, list):
    #    return "$const-list %r" % (val,)
    #    #return "new ArrayList<%s>{{%s}}" % (typ.oftype, body,)
    #elif isinstance(val, dict):
    #    return "$const-map %r " % (val,)
    else:
        raise IDLError("%r cannot be converted to a java const" % (val,))


class JavaTarget(TargetBase):
    DEFAULT_TARGET_DIR = "."
    
    @contextmanager
    def new_module(self, filename):
        mod = clike.Module()
        yield mod
        with self.open(filename, "w") as f:
            f.write(mod.render())

    def generate(self, service):
        with self.new_module("%sBindings.java" % (service.name,)) as module:
            BLOCK = module.block
            STMT = module.stmt
            SEP = module.sep
            DOC = module.doc
            
            STMT("package {0}Bindings", service.name)
            SEP()
            STMT("import java.util.*")
            STMT("import java.io.*")
            STMT("import java.net.*;")
            STMT("import agnos.*")
            SEP()
            with BLOCK("public class {0}Bindings", service.name):
                STMT('public static final String AGNOS_VERSION = "Agnos 1.0"')
                STMT('public static final String IDL_MAGIC = "{0}"', service.digest)

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
                    STMT("public final static {0} {1} = {2}", type_to_java(member.type), 
                        member.name, const_to_java(member.type, member.value))
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
            return "new Packers.ListOf<%s>(%s, %s)" % (type_to_java(tp), tp.id, 
                self._generate_templated_packer_for_type(tp.oftype),)
        elif isinstance(tp, compiler.TMap):
            return "new Packers.MapOf<%s, %s>(%s, %s, %s)" % (type_to_java(tp.keytype), 
                type_to_java(tp.valtype), tp.id, self._generate_templated_packer_for_type(tp.keytype),
                self._generate_templated_packer_for_type(tp.valtype))
        else:
            return type_to_packer(tp)

    def generate_templated_packers_decl(self, module, service):
        BLOCK = module.block
        STMT = module.stmt
        SEP = module.sep
        
        for tp in service.all_types:
            if isinstance(tp, (compiler.TList, compiler.TMap)):
                STMT("protected Packers.AbstractPacker _{0}", tp.stringify())

    def generate_templated_packers_impl(self, module, service):
        BLOCK = module.block
        STMT = module.stmt
        SEP = module.sep
        
        for tp in service.all_types:
            if isinstance(tp, (compiler.TList, compiler.TMap)):
                STMT("_{0} = {1}", tp.stringify(), self._generate_templated_packer_for_type(tp))
    
    def generate_enum(self, module, enum):
        BLOCK = module.block
        STMT = module.stmt
        SEP = module.sep
        with BLOCK("public enum {0}", enum.name):
            for mem in enum.members[:-1]:
                STMT("{0} ({1})", mem.name, mem.value, suffix = ",")
            STMT("{0} ({1})", enum.members[-1].name, enum.members[-1].value)
            SEP()
            STMT("public Integer value")
            with BLOCK("private static final Map<Integer, {0}> _BY_VALUE = new HashMap<Integer, {0}>()", 
                    enum.name, prefix = "{{", suffix = "}};"):
                with BLOCK("for({0} member : {0}.values())", enum.name):
                    STMT("put(member.value, member)")
            SEP()
            with BLOCK("private {0}(int v)", enum.name):
                STMT("value = new Integer(v)")
            with BLOCK("public static {0} getByValue(Integer val)", enum.name):
                STMT("return _BY_VALUE.get(val)")
        SEP()
        with BLOCK("protected static class _{0}Packer extends Packers.AbstractPacker", enum.name):
            with BLOCK("public int getId()"):
                STMT("return {0}", enum.id)
            with BLOCK("public void pack(Object obj, OutputStream stream) throws IOException"):
                STMT("Packers.Int32.pack((({0})obj).value, stream)", enum.name)
            with BLOCK("public Object unpack(InputStream stream) throws IOException"):
                STMT("return {0}.getByValue((Integer)Packers.Int32.unpack(stream))", enum.name)
        SEP()
        STMT("protected static _{0}Packer {0}Packer = new _{0}Packer()", enum.name)

    def generate_record_class(self, module, rec):
        BLOCK = module.block
        STMT = module.stmt
        SEP = module.sep
        if isinstance(rec, compiler.Exception):
            extends = "extends Protocol.PackedException"
        else:
            extends = ""
        SEP()
        with BLOCK("public static class {0} {1}", rec.name, extends):
            for mem in rec.members:
                STMT("public {0} {1}", type_to_java(mem.type), mem.name)
            SEP()
            with BLOCK("public {0}()", rec.name):
                pass
            if rec.members:
                args = ", ".join("%s %s" % (type_to_java(mem.type), mem.name) for mem in rec.members)
                with BLOCK("public {0}({1})", rec.name, args):
                    for mem in rec.members:
                        STMT("this.{0} = {0}", mem.name)
            with BLOCK("public String toString()"):
                if not rec.members:
                    STMT('return "{0}()"', rec.name)
                else:
                    STMT('return "{0}(" + {1} + ")"', rec.name, ' + ", " + '.join(mem.name  for mem in rec.members))
    
    def generate_record_packer(self, module, rec, static):
        BLOCK = module.block
        STMT = module.stmt
        SEP = module.sep
        with BLOCK("protected {0}class _{1}Packer extends Packers.AbstractPacker", 
                "static " if static else "", rec.name):
            with BLOCK("public int getId()"):
                STMT("return {0}", rec.id)
            with BLOCK("public void pack(Object obj, OutputStream stream) throws IOException"):
                STMT("{0} val = ({0})obj", rec.name)
                for mem in rec.members:
                    STMT("{0}.pack(val.{1}, stream)", type_to_packer(mem.type), mem.name)
            with BLOCK("public Object unpack(InputStream stream) throws IOException"):
                with BLOCK("return new {0}(", rec.name, prefix = "", suffix = ");"):
                    for mem in rec.members[:-1]:
                        STMT("({0}){1}.unpack(stream)", type_to_java(mem.type), 
                            type_to_packer(mem.type), suffix = ",")
                    if rec.members:
                        mem = rec.members[-1]
                        STMT("({0}){1}.unpack(stream)", type_to_java(mem.type), 
                            type_to_packer(mem.type), suffix = "")
        SEP()
        if static:
            STMT("protected static _{0}Packer {0}Packer = new _{0}Packer()", rec.name)
        else:
            STMT("protected _{0}Packer {0}Packer", rec.name)

    def generate_class_interface(self, module, cls):
        BLOCK = module.block
        STMT = module.stmt
        SEP = module.sep
        DOC = module.doc
        if cls.extends:
            extends = " extends " + ", ".join("I%s" % (c.name,) for c in cls.extends)
        else:
            extends = ""
        with BLOCK("public interface I{0}{1}", cls.name, extends):
            if cls.attrs:
                DOC("attributes")
            for attr in cls.attrs:
                if attr.get:
                    STMT("{0} get_{1}() throws Exception", type_to_java(attr.type), attr.name)
                if attr.set:
                    STMT("void set_{0}({1} value) throws Exception", attr.name, type_to_java(attr.type))
            if cls.attrs:
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
            with BLOCK("protected BaseProxy(Client client, Long objref, boolean owns_ref)"):
                STMT("_client = client")
                STMT("_objref = objref")
                STMT("_disposed = owns_ref ? false : true")
            SEP()
            with BLOCK("protected void finalize()"):
                STMT("dispose()")
            SEP()
            with BLOCK("public void dispose()"):
                with BLOCK("if (_disposed)"):
                    STMT("return")
                with BLOCK("synchronized (this)"):
                    STMT("_disposed = true")
                    STMT("_client._utils.decref(_objref)")
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
        module.stmt("/**", suffix = "")
        for line in text.splitlines():
            module.stmt(" * {0}", line.strip(), suffix = "")
        module.stmt(" */", suffix = "")

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
        with BLOCK("public static class {0}Proxy extends BaseProxy implements I{0}", cls.name):
            with BLOCK("protected {0}Proxy(Client client, Long objref, boolean owns_ref)", cls.name):
                STMT("super(client, objref, owns_ref)")
            SEP()
            for attr in cls.all_attrs:
                if attr.get:
                    self.emit_javadoc(["Getter for %s" % (attr.name,), attr.doc], module)
                    with BLOCK("public {0} get_{1}() throws Exception", type_to_java(attr.type), attr.name):
                        STMT("return ({0})(_client._funcs.sync_{1}(this))", type_to_java(attr.type), attr.getter.id)
                if attr.set:
                    self.emit_javadoc(["Setter for %s" % (attr.name,), attr.doc], module)
                    with BLOCK("public void set_{0}({1} value) throws Exception", 
                            attr.name, type_to_java(attr.type)):
                        STMT("_client._funcs.sync_{0}(this, value)", attr.setter.id)
            SEP()
            for method in cls.all_methods:
                self.emit_func_javadoc(method, module)
                args = ", ".join("%s %s" % (type_to_java(arg.type), arg.name) for arg in method.args)
                with BLOCK("public {0} {1}({2}) throws Exception", type_to_java(method.type), method.name, args):
                    callargs = ["this"] + [
                        "(%s)%s" % (type_to_java(arg.type, proxy=True), arg.name) 
                            if isinstance(arg.type, compiler.Class) else arg.name 
                        for arg in method.args]
                    if method.type == compiler.t_void:
                        STMT("_client._funcs.sync_{0}({1})", method.func.id, ", ".join(callargs))
                    else:
                        STMT("return ({0})_client._funcs.sync_{1}({2})", type_to_java(method.type),
                            method.func.id, ", ".join(callargs))
            if cls.all_derived:
                SEP()
                DOC("downcasts")
                for cls2 in cls.all_derived:
                    with BLOCK("public {0} castTo{1}()", type_to_java(cls2, proxy = True), cls2.name):
                        STMT("return new {0}(_client, _objref, false)", type_to_java(cls2, proxy = True))
            if cls.all_bases:
                SEP()
                DOC("upcasts")
                for cls2 in cls.all_bases:
                    with BLOCK("public {0} castTo{1}()", type_to_java(cls2, proxy = True), cls2.name):
                        STMT("return new {0}(_client, _objref, false)", type_to_java(cls2, proxy = True))

    def generate_handler_interface(self, module, service):
        BLOCK = module.block
        STMT = module.stmt
        SEP = module.sep
        with BLOCK("public interface IHandler"):
            for member in service.funcs.values():
                if isinstance(member, compiler.Func):
                    args = ", ".join("%s %s" % (type_to_java(arg.type), arg.name) for arg in member.args)
                    STMT("{0} {1}({2}) throws Exception", type_to_java(member.type), member.fullname, args)

    def generate_processor(self, module, service):
        BLOCK = module.block
        STMT = module.stmt
        SEP = module.sep

        with BLOCK("public static class Processor extends Protocol.BaseProcessor"):
            STMT("protected IHandler handler")
            SEP()
            for tp in service.types.values():
                if isinstance(tp, compiler.Class):
                    STMT("protected Packers.ObjRef {0}ObjRef", tp.name)
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
                    STMT("{0}Packer = new _{0}Packer()", rec.name)
                self.generate_templated_packers_impl(module, service)
                SEP()
                STMT("HashMap<Integer, Packers.AbstractPacker> packersMap = new HashMap<Integer, Packers.AbstractPacker>()")
                for tp in service.types.values():
                    STMT("packersMap.put({0}, {1})", tp.id, type_to_packer(tp))
                STMT("heteroMapPacker = new Packers.HeteroMapPacker(999, packersMap)")
                STMT("packersMap.put(999, heteroMapPacker)")
                
            SEP()
            self.generate_process_getinfo(module, service)
            SEP()
            self.generate_process_invoke(module, service)

    def generate_process_getinfo(self, module, service):
        BLOCK = module.block
        STMT = module.stmt
        SEP = module.sep
        
        with BLOCK("protected void processGetGeneralInfo(HeteroMap map)"):
            STMT('map.put("AGNOS_VERSION", AGNOS_VERSION)')
            STMT('map.put("IDL_MAGIC", IDL_MAGIC)')
            STMT('map.put("SERVICE_NAME", "{0}")', service.name)
        SEP()
        with BLOCK("protected void processGetFunctionsInfo(HeteroMap map)"):
            STMT("HeteroMap funcinfo")
            STMT("HashMap<String, String> args")
            STMT("HashMap<String, String> anno")
            SEP()
            for func in service.funcs.values():
                STMT("funcinfo = new HeteroMap()")
                STMT('funcinfo.put("name", "{0}")', func.name)
                STMT('funcinfo.put("type", "{0}")', str(func.type))
                STMT("args = new HashMap<String, String>()")
                for arg in func.args:
                    STMT('args.put("{0}", "{1}")', arg.name, str(arg.type))
                STMT('funcinfo.put("args", args, Packers.mapOfStrStr)')
                if func.annotations:
                    STMT("anno = new HashMap<String, String>()")
                    for anno in func.annotations:
                        STMT('anno.put("{0}", "{1}")', anno.name, anno.value)
                    STMT('funcinfo.put("annotations", anno, Packers.mapOfStrStr)')
                STMT('map.put({0}, funcinfo, Packers.builtinHeteroMapPacker)', func.id)
        SEP()
        with BLOCK("protected void processGetFunctionCodes(HeteroMap map)"):
            for func in service.funcs.values():
                STMT('map.put("{0}", {1})', func.name, func.id)    
    
    def generate_process_invoke(self, module, service):
        BLOCK = module.block
        STMT = module.stmt
        SEP = module.sep

        with BLOCK("protected void processInvoke(Transports.ITransport transport, int seq) throws Exception"):
            STMT("Packers.AbstractPacker packer = null")
            STMT("Object result = null")
            STMT("Object inst = null")
            STMT("Object[] args = null")
            STMT("InputStream inStream = transport.getInputStream()")
            STMT("OutputStream outStream = transport.getOutputStream()")
            STMT("int funcid = (Integer){0}.unpack(inStream)", type_to_packer(compiler.t_int32))
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
                        STMT('throw new Protocol.ProtocolError("unknown function id: " + funcid)')
                SEP()
                STMT("{0}.pack(new Byte((byte)Protocol.REPLY_SUCCESS), outStream)", type_to_packer(compiler.t_int8))
                with BLOCK("if (packer != null)"):
                    STMT("packer.pack(result, outStream)")
            for tp in packed_exceptions:
                with BLOCK("catch ({0} ex)", tp.name):
                    STMT("transport.reset()")
                    STMT("{0}.pack(new Byte((byte)Protocol.REPLY_PACKED_EXCEPTION), outStream)", type_to_packer(compiler.t_int8))
                    STMT("{0}.pack({1}, outStream)", type_to_packer(compiler.t_int32), tp.id)
                    STMT("{0}.pack(ex, outStream)", type_to_packer(tp))

    def generate_invocation_case(self, module, func):
        BLOCK = module.block
        STMT = module.stmt
        SEP = module.sep
        
        if isinstance(func, compiler.Func):
            if func.args:
                with BLOCK("args = new Object[] {0}", "{", prefix = "", suffix = "};"):
                    for arg in func.args[:-1]:
                        STMT("{0}.unpack(inStream)", type_to_packer(arg.type), suffix = ",")
                    if func.args:
                        arg = func.args[-1]
                        STMT("{0}.unpack(inStream)", type_to_packer(arg.type), suffix = ",")
            callargs = ", ".join("(%s)args[%s]" % (type_to_java(arg.type), i) for i, arg in enumerate(func.args))
            if func.type == compiler.t_void:
                invocation = "handler.%s" % (func.fullname,) 
            else:
                invocation = "result = handler.%s" % (func.fullname,)
        else:
            insttype = func.args[0].type
            STMT("inst = ({0})({1}.unpack(inStream))", 
                type_to_java(insttype), type_to_packer(insttype))

            if len(func.args) > 1:
                with BLOCK("args = new Object[] {0}", "{", prefix = "", suffix = "};"):
                    for arg in func.args[1:-1]:
                        STMT("{0}.unpack(inStream)", type_to_packer(arg.type), suffix = ",")
                    arg = func.args[-1]
                    STMT("{0}.unpack(inStream)", type_to_packer(arg.type), suffix = ",")
            callargs = ", ".join("(%s)args[%s]" % (type_to_java(arg.type), i) for i, arg in enumerate(func.args[1:]))
            
            if isinstance(func.origin, compiler.ClassAttr):
                if func.type == compiler.t_void:
                    invocation = "((%s)inst).set_%s" % (type_to_java(insttype), func.origin.name,)
                else:
                    invocation = "result = ((%s)inst).get_%s" % (type_to_java(insttype), func.origin.name,)
            else:
                if func.type == compiler.t_void:
                    invocation = "((%s)inst).%s" % (type_to_java(insttype), func.origin.name,)
                else:
                    invocation = "result = ((%s)inst).%s" % (type_to_java(insttype), func.origin.name,)
        
        with BLOCK("try {0}", "{", prefix = ""):
            STMT("{0}({1})", invocation, callargs)
        with BLOCK("catch (Protocol.PackedException ex) {0}", "{", prefix = ""):
            STMT("throw ex")
        with BLOCK("catch (Exception ex) {0}", "{", prefix = ""):
            STMT("throw new Protocol.GenericException(ex.toString(), getExceptionTraceback(ex))")

    #===========================================================================
    # client
    #===========================================================================
        
    def generate_client(self, module, service):
        BLOCK = module.block
        STMT = module.stmt
        SEP = module.sep
        DOC = module.doc
        
        with BLOCK("public static class Client extends Protocol.BaseClient"):
            for tp in service.types.values():
                if isinstance(tp, compiler.Class):
                    STMT("protected Packers.ObjRef {0}ObjRef", tp.name)
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
            with BLOCK("protected abstract class ClientSerializer implements Packers.ISerializer"):
                with BLOCK("public Long store(Object obj)"):
                    with BLOCK("if (obj == null)"):
                        STMT("return new Long(-1)")
                    STMT("return ((BaseProxy)obj)._objref")
                SEP()
                with BLOCK("public Object load(Long id)"):
                    with BLOCK("if (id < 0)"):
                        STMT("return null")
                    STMT("return _get_proxy(id)")
                SEP()
                STMT("protected abstract Object _get_proxy(Long id)")
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
        with BLOCK("public Client(Transports.ITransport transport) throws Exception"):
            STMT("Map<Integer, Packers.AbstractPacker> pem = new HashMap<Integer, Packers.AbstractPacker>()") 
            STMT("_utils = new Protocol.ClientUtils(transport, pem)")
            STMT("_funcs = new _Functions(_utils)")
            SEP()
            STMT("final Client the_client = this")
            for tp in service.types.values():
                if isinstance(tp, compiler.Class):
                    with BLOCK("{0}ObjRef = new Packers.ObjRef({1}, new ClientSerializer() {2}", 
                            tp.name, tp.id, "{", prefix = "", suffix = "});"):
                        with BLOCK("protected Object _get_proxy(Long id)"):
                            STMT("Object proxy = the_client._utils.getProxy(id)")
                            with BLOCK("if (proxy == null)"):
                                STMT("proxy = new {0}(the_client, id, true)", type_to_java(tp, proxy = True))
                                STMT("the_client._utils.cacheProxy(id, proxy)")
                            STMT("return proxy")
                    SEP()
            for rec in generated_records:
                STMT("{0}Packer = new _{0}Packer()", rec.name)
            self.generate_templated_packers_impl(module, service)
            SEP()
            for mem in service.types.values():
                if isinstance(mem, compiler.Exception):
                    STMT("pem.put({0}, {1}Packer)", mem.id, mem.name)
            SEP()
            for name, id in namespaces:
                STMT("{0} = new _Namespace{1}(_funcs)", name, id)
            SEP()
            STMT("HashMap<Integer, Packers.AbstractPacker> packersMap = new HashMap<Integer, Packers.AbstractPacker>()")
            for tp in service.types.values():
                STMT("packersMap.put({0}, {1})", tp.id, type_to_packer(tp))
                STMT("heteroMapPacker = new Packers.HeteroMapPacker(999, packersMap)")
            STMT("packersMap.put(999, heteroMapPacker)")

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
            STMT("protected _Functions _funcs")
            SEP()
            for name, node in root.iteritems():
                if isinstance(node, dict):
                    self.generate_client_namespace_classes(module, node)
                    subnamespaces.append((name, node["__id__"]))
                elif isinstance(node, compiler.Func):
                    func = node
                    args = ", ".join("%s %s" % (type_to_java(arg.type, proxy = False), arg.name) for arg in func.args)
                    callargs = ", ".join(arg.name for arg in func.args)
                    with BLOCK("public {0} {1}({2}) throws Exception", type_to_java(func.type, proxy = True), func.name, args):
                        if func.type == compiler.t_void:
                            STMT("_funcs.sync_{0}({1})", func.id, callargs)
                        else:
                            STMT("return _funcs.sync_{0}({1})", func.id, callargs)
            SEP()
            with BLOCK("protected _Namespace{0}(_Functions funcs)", root["__id__"]):
                STMT("_funcs = funcs")
                for name, id in subnamespaces:
                    STMT("{0} = new _Namespace{1}(funcs)", name, id)
        STMT("public _Namespace{0} {1}", root["__id__"], root["__name__"])

    def generate_client_factories(self, module, service):
        BLOCK = module.block
        STMT = module.stmt
        SEP = module.sep
        
        with BLOCK("public static Client connectSock(String host, int port) throws Exception"):
            STMT("return new Client(new Transports.SocketTransport(host, port))")
        with BLOCK("public static Client connectSock(Socket sock) throws Exception"):
            STMT("return new Client(new Transports.SocketTransport(sock))")
        
        with BLOCK("public static Client connectProc(String executable) throws Exception"):
            STMT("return new Client(Transports.ProcTransport.connect(executable))")
        with BLOCK("public static Client connectProc(ProcessBuilder procbuilder) throws Exception"):
            STMT("return new Client(Transports.ProcTransport.connect(procbuilder))")

        with BLOCK("public static Client connectUrl(String url) throws Exception"):
            STMT("return new Client(new Transports.HttpClientTransport(url))")
        with BLOCK("public static Client connectUrl(URL url) throws Exception"):
            STMT("return new Client(new Transports.HttpClientTransport(url))")

    def generate_client_internal_funcs(self, module, service):
        BLOCK = module.block
        STMT = module.stmt
        SEP = module.sep
        DOC = module.doc
        with BLOCK("protected class _Functions"):
            STMT("protected Protocol.ClientUtils utils")
            with BLOCK("public _Functions(Protocol.ClientUtils utils)"):
                STMT("this.utils = utils")
            SEP()
            for func in service.funcs.values():
                args = ", ".join("%s %s" % (type_to_java(arg.type, proxy = False), arg.name) for arg in func.args)
                with BLOCK("public {0} sync_{1}({2}) throws Exception", type_to_java(func.type, proxy = True), func.id, args):
                    STMT("int seq = utils.beginCall({0}, {1})", func.id, type_to_packer(func.type))
                    STMT("OutputStream outStream = utils.transport.getOutputStream()")
                    with BLOCK("try"):
                        for arg in func.args:
                            STMT("{0}.pack({1}, outStream)", type_to_packer(arg.type), arg.name)
                    with BLOCK("catch (Exception ex)"):
                        STMT("utils.cancelCall()")
                        STMT("throw ex")
                    STMT("utils.endCall()")
                    STMT("Object res = utils.getReply(seq)")
                    if func.type != compiler.t_void:
                        STMT("return ({0})res", type_to_java(func.type, proxy = True))
                SEP()
        SEP()
        STMT("protected _Functions _funcs")

    def generate_client_funcs(self, module, service):
        BLOCK = module.block
        STMT = module.stmt
        SEP = module.sep
        DOC = module.doc
        for func in service.funcs.values():
            if not isinstance(func, compiler.Func) or func.namespace:
                continue
            args = ", ".join("%s %s" % (type_to_java(arg.type, proxy = True), arg.name) for arg in func.args)
            callargs = ", ".join(arg.name for arg in func.args)
            self.emit_func_javadoc(func, module)
            with BLOCK("public {0} {1}({2}) throws Exception", type_to_java(func.type, proxy = True), func.name, args):
                if func.type == compiler.t_void:
                    STMT("_funcs.sync_{0}({1})", func.id, callargs)
                else:
                    STMT("return _funcs.sync_{0}({1})", func.id, callargs)
            SEP()
    








