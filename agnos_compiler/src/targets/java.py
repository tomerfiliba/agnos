import itertools
import os
from .base import TargetBase, NOOP
from .. import compiler
from ..compiler import is_complex_type


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
        return "HeteroMap"
    elif isinstance(t, compiler.TList):
        return "List<%s>" % (type_to_java(t.oftype, proxy = proxy),)
    elif isinstance(t, compiler.TSet):
        return "Set<%s>" % (type_to_java(t.oftype, proxy = proxy),)
    elif isinstance(t, compiler.TMap):
        return "Map<%s, %s>" % (type_to_java(t.keytype, proxy = proxy), 
            type_to_java(t.valtype, proxy = proxy))
    elif isinstance(t, (compiler.Enum, compiler.Record, compiler.Exception)):
        return "%s" % (t.name,)
    elif isinstance(t, compiler.Class):
        if proxy:
            return "%sProxy" % (t.name,)
        else:
            return "I%s" % (t.name,)
    else:
        assert False

def type_to_java_full(t, service, proxy = False):
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
        return "HeteroMap"
    elif isinstance(t, compiler.TList):
        return "List<%s>" % (type_to_java_full(t.oftype, service, proxy = proxy),)
    elif isinstance(t, compiler.TSet):
        return "Set<%s>" % (type_to_java_full(t.oftype, service, proxy = proxy),)
    elif isinstance(t, compiler.TMap):
        return "Map<%s, %s>" % (type_to_java_full(t.keytype, service, proxy = proxy), 
            type_to_java_full(t.valtype, service, proxy = proxy))
    elif isinstance(t, (compiler.Enum, compiler.Record, compiler.Exception)):
        return "%s.%s" % (service.name, t.name,)
    elif isinstance(t, compiler.Class):
        if proxy:
            return "%s.%sProxy" % (service.name, t.name,)
        else:
            return "%s.I%s" % (service.name, t.name,)
    else:
        assert False

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
    elif isinstance(t, (compiler.TList, compiler.TSet, compiler.TMap)):
        return "_%s" % (t.stringify(),)
    elif isinstance(t, (compiler.Enum, compiler.Record, compiler.Exception)):
        return "%sPacker" % (t.name,)
    elif isinstance(t, compiler.Class):
        return "%sObjRef" % (t.name,)
    else:
        assert False

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
    from ..langs import clike
    LANGUAGE = clike

    def generate(self, service):
        pkg = "%s.server_bindings" % (service.package,)
        dirs = pkg.replace(".", "/")
        
        self.mkdir(dirs)
        with self.new_module(os.path.join(dirs, "%s.java" % (service.name,))) as module:
            STMT = module.stmt
            SEP = module.sep
            
            STMT("package {0}", pkg)
            SEP()
            STMT("import java.util.*")
            STMT("import java.io.*")
            STMT("import java.net.*")
            STMT("import agnos.*")
            SEP()
            self.generate_server_bindings(module, service)
            SEP()

        pkg = "%s.client_bindings" % (service.package,)
        dirs = pkg.replace(".", "/")

        self.mkdir(dirs)
        with self.new_module(os.path.join(dirs, "%s.java" % (service.name,))) as module:
            STMT = module.stmt
            SEP = module.sep
            
            STMT("package {0}", pkg)
            SEP()
            STMT("import java.util.*")
            STMT("import java.io.*")
            STMT("import java.net.*")
            STMT("import agnos.*")
            SEP()
            self.generate_client_bindings(module, service)
            SEP()
        
        with self.new_module("%s_server.stub" % (service.name,)) as module:
            self.generate_server_stub(module, service)
            SEP()
    
    def generate_server_bindings(self, module, service):
        BLOCK = module.block
        STMT = module.stmt
        SEP = module.sep
        DOC = module.doc
        
        with BLOCK("public final class {0}", service.name):
            STMT('public static final String AGNOS_TOOLCHAIN_VERSION = "{0}"', compiler.AGNOS_TOOLCHAIN_VERSION)
            STMT('public static final String AGNOS_PROTOCOL_VERSION = "{0}"', compiler.AGNOS_PROTOCOL_VERSION)
            STMT('public static final String IDL_MAGIC = "{0}"', service.digest)
            with BLOCK('public static final List<String> SUPPORTED_VERSIONS = new ArrayList<String>()',
                    prefix = "{{", suffix = "}};"):
                for ver in service.versions:
                    STMT('add("{0}")', ver)
            SEP()
            
            DOC("enums", spacer = True)
            for enum in service.enums():
                self.generate_enum(module, enum)
                SEP()
            
            DOC("records", spacer = True)
            for rec in service.records():
                self.generate_record_class(module, rec, proxy = False)
                SEP()
            
            for rec in service.records(lambda mem: not is_complex_type(mem)):
                self.generate_record_packer(module, rec, static = True, proxy = False)
                SEP()

            DOC("consts", spacer = True)
            for member in service.consts.values():
                STMT("public static final {0} {1} = {2}", type_to_java(member.type), 
                    member.fullname, const_to_java(member.type, member.value))
            SEP()
            
            DOC("classes", spacer = True)
            for cls in service.classes():
                self.generate_class_interface(module, cls)
                SEP()

            DOC("server implementation", spacer = True)
            self.generate_handler_interface(module, service)
            SEP()
            self.generate_processor(module, service)
            self.generate_processor_factory(module, service)
            SEP()
            
            DOC("$$extend-main$$")
            SEP()

    def generate_client_bindings(self, module, service):
        BLOCK = module.block
        STMT = module.stmt
        SEP = module.sep
        DOC = module.doc

        with BLOCK("public final class {0}", service.name):
            STMT('public static final String AGNOS_TOOLCHAIN_VERSION = "{0}"', compiler.AGNOS_TOOLCHAIN_VERSION)
            STMT('public static final String AGNOS_PROTOCOL_VERSION = "{0}"', compiler.AGNOS_PROTOCOL_VERSION)
            STMT('public static final String IDL_MAGIC = "{0}"', service.digest)
            if not service.clientversion:
                STMT("public static final String CLIENT_VERSION = null")
            else:
                STMT('public static final String CLIENT_VERSION = "{0}"', service.clientversion)

            SEP()
            
            DOC("enums", spacer = True)
            for enum in service.enums():
                self.generate_enum(module, enum)
                SEP()
            
            DOC("records", spacer = True)
            for rec in service.records():
                self.generate_record_class(module, rec, proxy = True)
                SEP()
            
            for rec in service.records(lambda mem: not is_complex_type(mem)):
                self.generate_record_packer(module, rec, static = True, proxy = True)
                SEP()

            DOC("consts", spacer = True)
            for member in service.consts.values():
                if not member.namespace:
                    STMT("public static final {0} {1} = {2}", type_to_java(member.type), 
                        member.name, const_to_java(member.type, member.value))
            SEP()
            
            DOC("classes", spacer = True)
            self.generate_base_class_proxy(module, service)
            SEP()
            for cls in service.classes():
                self.generate_class_proxy(module, service, cls)
                SEP()
            
            DOC("client", spacer = True)
            self.generate_client(module, service)
            SEP()
            
            DOC("$$extend-main$$")
            SEP()

    def _generate_templated_packer_for_type(self, tp, proxy):
        if isinstance(tp, compiler.TList):
            return "new Packers.ListOf<%s>(%s, %s)" % (type_to_java(tp, proxy = proxy), 
                tp.id, self._generate_templated_packer_for_type(tp.oftype, proxy = proxy),)
        elif isinstance(tp, compiler.TSet):
            return "new Packers.SetOf<%s>(%s, %s)" % (type_to_java(tp, proxy = proxy), 
                tp.id, self._generate_templated_packer_for_type(tp.oftype, proxy = proxy),)
        elif isinstance(tp, compiler.TMap):
            return "new Packers.MapOf<%s, %s>(%s, %s, %s)" % (type_to_java(tp.keytype, proxy = proxy), 
                type_to_java(tp.valtype, proxy = proxy), 
                tp.id, 
                self._generate_templated_packer_for_type(tp.keytype, proxy = proxy),
                self._generate_templated_packer_for_type(tp.valtype, proxy = proxy))
        else:
            return type_to_packer(tp)

    def generate_templated_packers_decl(self, module, service):
        BLOCK = module.block
        STMT = module.stmt
        SEP = module.sep
        
        for tp in service.all_types:
            if isinstance(tp, (compiler.TList, compiler.TSet, compiler.TMap)):
                STMT("protected final Packers.AbstractPacker _{0}", tp.stringify())

    def generate_templated_packers_impl(self, module, service, proxy):
        BLOCK = module.block
        STMT = module.stmt
        SEP = module.sep
        
        for tp in service.all_types:
            if isinstance(tp, (compiler.TList, compiler.TSet, compiler.TMap)):
                STMT("_{0} = {1}", tp.stringify(), self._generate_templated_packer_for_type(tp, proxy = proxy))
    
    def generate_enum(self, module, enum):
        BLOCK = module.block
        STMT = module.stmt
        SEP = module.sep
        with BLOCK("public enum {0}", enum.name):
            for mem in enum.members[:-1]:
                STMT("{0} ({1})", mem.name, mem.value, suffix = ",")
            STMT("{0} ({1})", enum.members[-1].name, enum.members[-1].value)
            SEP()
            STMT("public final Integer value")
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

    def generate_record_class(self, module, rec, proxy):
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
                STMT("public {0} {1}", type_to_java(mem.type, proxy = proxy), mem.name)
            SEP()
            with BLOCK("public {0}()", rec.name):
                pass
            if rec.members:
                args = ", ".join("%s %s" % (type_to_java(mem.type, proxy = proxy), mem.name) 
                    for mem in rec.members)
                with BLOCK("public {0}({1})", rec.name, args):
                    for mem in rec.members:
                        STMT("this.{0} = {0}", mem.name)
            with BLOCK("public String toString()"):
                if not rec.members:
                    STMT('return "{0}()"', rec.name)
                else:
                    STMT('return "{0}(" + {1} + ")"', rec.name, 
                        ' + ", " + '.join(mem.name  for mem in rec.members))
    
    def generate_record_packer(self, module, rec, static, proxy):
        BLOCK = module.block
        STMT = module.stmt
        SEP = module.sep
        with BLOCK("protected final {0}class _{1}Packer extends Packers.AbstractPacker", 
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
                        STMT("({0}){1}.unpack(stream)", type_to_java(mem.type, proxy = proxy), 
                            type_to_packer(mem.type), suffix = ",")
                    if rec.members:
                        mem = rec.members[-1]
                        STMT("({0}){1}.unpack(stream)", type_to_java(mem.type, proxy = proxy), 
                            type_to_packer(mem.type), suffix = "")
        SEP()
        if static:
            STMT("protected static final _{0}Packer {0}Packer = new _{0}Packer()", rec.name)
        else:
            STMT("protected final _{0}Packer {0}Packer", rec.name)

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
                    STMT("void set_{0}({1} value) throws Exception", attr.name, 
                        type_to_java(attr.type))
            if cls.attrs:
                SEP()
            if cls.methods:
                DOC("methods")
            for method in cls.methods:
                args = ", ".join("%s %s" % (type_to_java(arg.type), arg.name) 
                    for arg in method.args)
                STMT("{0} {1}({2}) throws Exception", type_to_java(method.type), 
                    method.name, args)

    def generate_base_class_proxy(self, module, service):
        BLOCK = module.block
        STMT = module.stmt
        SEP = module.sep
        DOC = module.doc
        with BLOCK("public static abstract class BaseProxy"):
            STMT("protected final Long _objref")
            STMT("protected final Client _client")
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
        with BLOCK("public static class {0}Proxy extends BaseProxy", cls.name):
            with BLOCK("protected {0}Proxy(Client client, Long objref, boolean owns_ref)", cls.name):
                STMT("super(client, objref, owns_ref)")
            SEP()
            for attr in cls.all_attrs:
                if attr.get:
                    #self.emit_javadoc(["Getter for %s" % (attr.name,), attr.doc], module)
                    with BLOCK("public {0} get_{1}() throws Exception", 
                            type_to_java(attr.type, proxy = True), attr.name):
                        STMT("return _client._funcs.sync_{0}(this)", attr.getter.id)
                if attr.set:
                    #self.emit_javadoc(["Setter for %s" % (attr.name,), attr.doc], module)
                    with BLOCK("public void set_{0}({1} value) throws Exception", 
                            attr.name, type_to_java(attr.type, proxy = True)):
                        STMT("_client._funcs.sync_{0}(this, value)", attr.setter.id)
            SEP()
            for method in cls.all_methods:
                if not method.clientside:
                    continue
                #self.emit_func_javadoc(method, module)
                args = ", ".join("%s %s" % (type_to_java(arg.type, proxy = True), arg.name) 
                    for arg in method.args)
                with BLOCK("public {0} {1}({2}) throws Exception", 
                        type_to_java(method.type, proxy = True), method.name, args):
                    callargs = ["this"] + [arg.name for arg in method.args]
                    if method.type == compiler.t_void:
                        STMT("_client._funcs.sync_{0}({1})", method.func.id, ", ".join(callargs))
                    else:
                        STMT("return _client._funcs.sync_{0}({1})", method.func.id, ", ".join(callargs))
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
                    args = ", ".join("%s %s" % (type_to_java(arg.type), arg.name) 
                        for arg in member.args)
                    STMT("{0} {1}({2}) throws Exception", type_to_java(member.type),
                        member.fullname, args)

    def generate_processor(self, module, service):
        BLOCK = module.block
        STMT = module.stmt
        SEP = module.sep
        DOC = module.doc

        with BLOCK("public static class Processor extends Protocol.BaseProcessor"):
            STMT("protected final IHandler handler")
            SEP()
            for cls in service.classes():
                STMT("protected final Packers.ObjRef {0}ObjRef", cls.name)
            SEP()
            generated_records = []
            for rec in service.records(is_complex_type):
                self.generate_record_packer(module, rec, static = False, proxy = False)
                generated_records.append(rec)
                SEP()
            self.generate_templated_packers_decl(module, service)
            SEP()
            STMT("protected final Packers.HeteroMapPacker heteroMapPacker")
            SEP()
            with BLOCK("public Processor(Transports.ITransport transport, IHandler handler)"):
                STMT("super(transport)")
                STMT("this.handler = handler")
                for cls in service.classes():
                    STMT("{0}ObjRef = new Packers.ObjRef({1}, this)", cls.name, cls.id)
                for rec in generated_records:
                    STMT("{0}Packer = new _{0}Packer()", rec.name)
                self.generate_templated_packers_impl(module, service, proxy = False)
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
            SEP()
            DOC("$$extend-processor$$")
            SEP()
        
    def generate_processor_factory(self, module, service):
        BLOCK = module.block
        STMT = module.stmt
        SEP = module.sep
        
        with BLOCK("public static class ProcessorFactory implements Protocol.IProcessorFactory"):
            STMT("protected IHandler handler")
            with BLOCK("public ProcessorFactory(IHandler handler)"):
                STMT("this.handler = handler")
            with BLOCK("public Protocol.BaseProcessor create(Transports.ITransport transport)"):
                STMT("return new Processor(transport, this.handler)")
        SEP()

    def generate_process_getinfo(self, module, service):
        BLOCK = module.block
        STMT = module.stmt
        SEP = module.sep
        
        with BLOCK("protected void processGetGeneralInfo(HeteroMap map)"):
            STMT('map.put("AGNOS_PROTOCOL_VERSION", AGNOS_PROTOCOL_VERSION)')
            STMT('map.put("AGNOS_TOOLCHAIN_VERSION", AGNOS_TOOLCHAIN_VERSION)')
            STMT('map.put("IDL_MAGIC", IDL_MAGIC)')
            STMT('map.put("SERVICE_NAME", "{0}")', service.name)
            STMT('map.put("SUPPORTED_VERSIONS", SUPPORTED_VERSIONS, Packers.listOfStr)')
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

        with BLOCK("protected void processInvoke(int seq) throws Exception"):
            STMT("Packers.AbstractPacker packer = null")
            STMT("Object result = null")
            STMT("Object inst = null")
            STMT("Object[] args = null")
            STMT("InputStream inStream = transport.getInputStream()")
            STMT("OutputStream outStream = transport.getOutputStream()")
            STMT("int funcid = (Integer){0}.unpack(inStream)", type_to_packer(compiler.t_int32))

            with BLOCK("try") if service.exceptions() else NOOP:
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
                STMT("{0}.pack(new Byte((byte)Protocol.REPLY_SUCCESS), outStream)", 
                    type_to_packer(compiler.t_int8))
                with BLOCK("if (packer != null)"):
                    STMT("packer.pack(result, outStream)")
            for tp in service.exceptions():
                with BLOCK("catch ({0} ex)", tp.name):
                    STMT("transport.reset()")
                    STMT("{0}.pack(new Byte((byte)Protocol.REPLY_PACKED_EXCEPTION), outStream)", 
                        type_to_packer(compiler.t_int8))
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
            callargs = ", ".join("(%s)args[%s]" % (type_to_java(arg.type), i) 
                for i, arg in enumerate(func.args))
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
            callargs = ", ".join("(%s)args[%s]" % (type_to_java(arg.type), i) 
                for i, arg in enumerate(func.args[1:]))
            
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
            for cls in service.classes():
                STMT("protected Packers.ObjRef {0}ObjRef", cls.name)
            SEP()
            generated_records = []
            for rec in service.records(is_complex_type):
                self.generate_record_packer(module, rec, static = False, proxy = True)
                generated_records.append(rec)
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
            STMT("protected final Packers.HeteroMapPacker heteroMapPacker")
            SEP()
            namespaces = self.generate_client_namespaces(module, service)
            SEP()
            self.generate_client_internal_funcs(module, service)
            SEP()
            self.generate_client_ctor(module, service, namespaces, generated_records)
            SEP()
            self.generate_client_funcs(module, service)
            SEP()
            self.generate_client_helpers(module, service)
            SEP()
            DOC("$$extend-client$$")
            SEP()
    
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
            for cls in service.classes():
                with BLOCK("{0}ObjRef = new Packers.ObjRef({1}, new ClientSerializer() {2}", 
                        cls.name, cls.id, "{", prefix = "", suffix = "});"):
                    with BLOCK("protected Object _get_proxy(Long id)"):
                        STMT("Object proxy = the_client._utils.getProxy(id)")
                        with BLOCK("if (proxy == null)"):
                            STMT("proxy = new {0}(the_client, id, true)", type_to_java(cls, proxy = True))
                            STMT("the_client._utils.cacheProxy(id, proxy)")
                        STMT("return proxy")
                    SEP()
            for rec in generated_records:
                STMT("{0}Packer = new _{0}Packer()", rec.name)
            self.generate_templated_packers_impl(module, service, proxy = True)
            SEP()
            for exc in service.exceptions():
                STMT("pem.put({0}, {1}Packer)", exc.id, exc.name)
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
            if isinstance(func, compiler.Func) and func.namespace and func.clientside:
                node = root
                fns = func.namespace.split(".")
                for part in fns:
                    if part not in node:
                        node[part] = {}
                        node[part]["__id__"] = nsid.next()
                        node[part]["__name__"] = part
                    node = node[part]
                node[func.name] = func

        for const in service.consts.values():
            if const.namespace:
                node = root
                fns = const.namespace.split(".")
                for part in fns:
                    if part not in node:
                        node[part] = {}
                        node[part]["__id__"] = nsid.next()
                        node[part]["__name__"] = part
                    node = node[part]
                node[const.name] = const
        
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
        with BLOCK("public static final class _Namespace{0}", root["__id__"]):
            subnamespaces = []
            STMT("protected final _Functions _funcs")
            SEP()
            for name, node in root.iteritems():
                if isinstance(node, dict):
                    self.generate_client_namespace_classes(module, node)
                    subnamespaces.append((name, node["__id__"]))
                elif isinstance(node, compiler.Func):
                    func = node
                    args = ", ".join("%s %s" % (type_to_java(arg.type, proxy = True), arg.name) 
                        for arg in func.args)
                    callargs = ", ".join(arg.name for arg in func.args)
                    with BLOCK("public {0} {1}({2}) throws Exception", 
                            type_to_java(func.type, proxy = True), func.name, args):
                        if func.type == compiler.t_void:
                            STMT("_funcs.sync_{0}({1})", func.id, callargs)
                        else:
                            STMT("return _funcs.sync_{0}({1})", func.id, callargs)
                elif isinstance(node, compiler.Const):
                    STMT("public static final {0} {1} = {2}", type_to_java(node.type), 
                        node.name, const_to_java(node.type, node.value))
                else:
                    pass
                    #raise TypeError("expected func or const, not %r" % (type(node),))
            SEP()
            with BLOCK("protected _Namespace{0}(_Functions funcs)", root["__id__"]):
                STMT("_funcs = funcs")
                for name, id in subnamespaces:
                    STMT("{0} = new _Namespace{1}(funcs)", name, id)
        STMT("public final _Namespace{0} {1}", root["__id__"], root["__name__"])

    def generate_client_helpers(self, module, service):
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
        
        SEP()
        with BLOCK("public void assertServiceCompatibility() throws IOException, Protocol.ProtocolError, Protocol.PackedException, Protocol.GenericException"):
            STMT("HeteroMap info = getServiceInfo(Protocol.INFO_GENERAL)")
            STMT('String agnos_protocol_version = (String)info.get("AGNOS_PROTOCOL_VERSION")')
            STMT('String service_name = (String)info.get("SERVICE_NAME")')
            
            with BLOCK('if (!agnos_protocol_version.equals(AGNOS_PROTOCOL_VERSION))'):
                STMT('''throw new Protocol.WrongAgnosVersion("expected protocol '" + AGNOS_PROTOCOL_VERSION + "', found '" + agnos_protocol_version + "'")''')
            with BLOCK('if (!service_name.equals("{0}"))', service.name):
                STMT('''throw new Protocol.WrongServiceName("expected service '{0}', found '" + service_name + "'")''', service.name)
            if service.clientversion:
                STMT('List<String> supported_versions = (List<String>)info.get("SUPPORTED_VERSIONS")')
                with BLOCK('if (supported_versions == null || !supported_versions.contains(CLIENT_VERSION))'):
                    STMT('''throw new Protocol.IncompatibleServiceVersion("server does not support client version '" + CLIENT_VERSION + "'")''')
    
    def generate_client_internal_funcs(self, module, service):
        BLOCK = module.block
        STMT = module.stmt
        SEP = module.sep
        DOC = module.doc
        with BLOCK("protected class _Functions"):
            STMT("protected final Protocol.ClientUtils utils")
            with BLOCK("public _Functions(Protocol.ClientUtils utils)"):
                STMT("this.utils = utils")
            SEP()
            for func in service.funcs.values():
                args = ", ".join("%s %s" % (type_to_java(arg.type, proxy = True), arg.name) 
                    for arg in func.args)
                with BLOCK("public {0} sync_{1}({2}) throws Exception", 
                        type_to_java(func.type, proxy = True), func.id, args):
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
        STMT("protected final _Functions _funcs")

    def generate_client_funcs(self, module, service):
        BLOCK = module.block
        STMT = module.stmt
        SEP = module.sep
        DOC = module.doc
        for func in service.funcs.values():
            if not isinstance(func, compiler.Func) or func.namespace or not func.clientside:
                continue
            args = ", ".join("%s %s" % (type_to_java(arg.type, proxy = True), arg.name) for arg in func.args)
            callargs = ", ".join(arg.name for arg in func.args)
            #self.emit_func_javadoc(func, module)
            with BLOCK("public {0} {1}({2}) throws Exception", 
                    type_to_java(func.type, proxy = True), func.name, args):
                if func.type == compiler.t_void:
                    STMT("_funcs.sync_{0}({1})", func.id, callargs)
                else:
                    STMT("return _funcs.sync_{0}({1})", func.id, callargs)
            SEP()

    ##########################################################################
    
    def generate_server_stub(self, module, service):
        BLOCK = module.block
        STMT = module.stmt
        SEP = module.sep
        DOC = module.doc

        STMT("import java.util.*")
        STMT("import {0}.server_bindings.{0}", service.package)
        SEP()
        
        with BLOCK("public class ServerStub"):
            DOC("classes", spacer = True)
            for cls in service.classes():
                with BLOCK("public static class {0} implements {1}", cls.name, type_to_java_full(cls, service)):
                    for attr in cls.all_attrs:
                        STMT("protected {0} _{1}", type_to_java_full(attr.type, service), attr.name)
                    SEP()
                    args = ", ".join("%s %s" % (type_to_java_full(attr.type, service), attr.name) for attr in cls.all_attrs)
                    with BLOCK("public {0}({1})", cls.name, args):
                        for attr in cls.all_attrs:
                            STMT("_{0} = {0}", attr.name)
                    SEP()
                    for attr in cls.all_attrs:
                        if attr.get:
                            with BLOCK("public {0} get_{1}() throws Exception", type_to_java_full(attr.type, service), attr.name):
                                STMT("return _{0}", attr.name)
                        if attr.set:
                            with BLOCK("public void set_{0}({1} value) throws Exception", attr.name, type_to_java_full(attr.type, service)):
                                STMT("_{0} = value", attr.name)
                        SEP()
                    for method in cls.all_methods:
                        args = ", ".join("%s %s" % (type_to_java_full(arg.type, service), arg.name) 
                            for arg in method.args)
                        with BLOCK("public {0} {1}({2}) throws Exception", type_to_java_full(method.type, service), method.name, args):
                            DOC("implement me")
                        SEP()
                SEP()
            DOC("handler", spacer = True)
            with BLOCK("public static class Handler implements {0}.IHandler", service.name):
                for member in service.funcs.values():
                    if not isinstance(member, compiler.Func):
                        continue
                    args = ", ".join("%s %s" % (type_to_java_full(arg.type, service), arg.name) 
                        for arg in member.args)
                    with BLOCK("public {0} {1}({2}) throws Exception", 
                            type_to_java_full(member.type, service), member.fullname, args):
                        DOC("implement me")
                    SEP()
            SEP()
            DOC("main", spacer = True)
            with BLOCK("public static void main(String[] args)"):
                STMT("agnos.Servers.CmdlineServer server = new agnos.Servers.CmdlineServer("
                    "new {0}.ProcessorFactory(new Handler()))", service.name)
                with BLOCK("try"):
                    STMT("server.main(args)")
                with BLOCK("catch (Exception ex)"):
                    STMT("ex.printStackTrace(System.err)")
            SEP()







