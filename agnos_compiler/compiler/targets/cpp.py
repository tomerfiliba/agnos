from .base import TargetBase, NOOP
from contextlib import contextmanager
import itertools
from .. import compiler
from ..compiler import is_complex_type, is_complicated_type



def type_to_cpp(t, proxy = False, shared = True, arg = False, ret = False):
    if t == compiler.t_void:
        return "void"
    elif t == compiler.t_bool:
        return "bool"
    elif t == compiler.t_int8:
        return "int8_t"
    elif t == compiler.t_int16:
        return "int16_t"
    elif t == compiler.t_int32:
        return "int32_t"
    elif t == compiler.t_int64:
        return "int64_t"
    elif t == compiler.t_float:
        return "double"
    elif t == compiler.t_string:
        if arg:
            return "const string&"
        elif ret:
            return "shared_ptr<string>"
        else:
            return "string"
    elif t == compiler.t_date:
        if arg:
            return "const datetime&"
        else:
            return "datetime"
    elif t == compiler.t_buffer:
        if arg:
            return "const string&"
        elif ret:
            return "shared_ptr<string>"
        else:
            return "string"
    elif t == compiler.t_heteromap:
        return "shared_ptr<HeteroMap>"
    elif isinstance(t, compiler.TList):
        return "shared_ptr< vector< %s > >" % (type_to_cpp(t.oftype, proxy = proxy, shared = shared),)
    elif isinstance(t, compiler.TSet):
        return "shared_ptr< set< %s > >" % (type_to_cpp(t.oftype, proxy = proxy, shared = shared),)
    elif isinstance(t, compiler.TMap):
        return "shared_ptr< map< %s, %s > >" % (type_to_cpp(t.keytype, proxy = proxy, shared = shared), 
            type_to_cpp(t.valtype, proxy = proxy, shared = shared))
    elif isinstance(t, compiler.Enum):
        return t.name
    elif isinstance(t, (compiler.Record, compiler.Exception)):
        if arg:
            return "const %s&" % (t.name,)
        elif ret:
            return "shared_ptr<%s>" % (t.name,)
        else:
            return t.name
    elif isinstance(t, compiler.Class):
        if proxy:
            return "%sProxy" % (t.name,)
        elif shared:
            return "shared_ptr<I%s>" % (t.name,)
        elif arg:
            return "const I%s&" % (t.name,)
        else:
            return "I%s" % (t.name,)
    else:
        assert False

def is_type_shared_ptr(t):
    if isinstance(t, compiler.Enum) or t in [compiler.t_void, compiler.t_bool, 
            compiler.t_int8, compiler.t_int16, compiler.t_int32, compiler.t_int64, 
            compiler.t_float, compiler.t_date]:
        return "false"
    else:
        return "true"

def type_to_packer(t):
    if t == compiler.t_void:
        return "void_packer"
    elif t == compiler.t_bool:
        return "bool_packer"
    elif t == compiler.t_int8:
        return "int8_packer"
    elif t == compiler.t_int16:
        return "int16_packer"
    elif t == compiler.t_int32:
        return "int32_packer"
    elif t == compiler.t_int64:
        return "int64_packer"
    elif t == compiler.t_float:
        return "float_packer"
    elif t == compiler.t_date:
        return "date_packer"
    elif t == compiler.t_buffer:
        return "buffer_packer"
    elif t == compiler.t_string:
        return "string_packer"
    elif t == compiler.t_heteromap:
        return "_heteromap_packer"
    elif isinstance(t, (compiler.TList, compiler.TSet, compiler.TMap)):
        return "_%s_packer" % (t.stringify(),)
    elif isinstance(t, (compiler.Enum, compiler.Record, compiler.Exception)):
        return "_%s_packer" % (t.name,)
    elif isinstance(t, compiler.Class):
        return "_%s_objref" % (t.name,)
    else:
        assert False

def type_to_packer_type(t, proxy = False):
    if t == compiler.t_void:
        return "VoidPacker"
    elif t == compiler.t_bool:
        return "BoolPacker"
    elif t == compiler.t_int8:
        return "Int8Packer"
    elif t == compiler.t_int16:
        return "Int16Packer"
    elif t == compiler.t_int32:
        return "Int32Packer"
    elif t == compiler.t_int64:
        return "Int64Packer"
    elif t == compiler.t_float:
        return "FloatPacker"
    elif t == compiler.t_date:
        return "DatePacker"
    elif t == compiler.t_buffer:
        return "BufferPacker"
    elif t == compiler.t_string:
        return "StringPacker"
    elif t == compiler.t_heteromap:
        return "HeteroMapPacker"
    elif isinstance(t, compiler.TList):
        return "ListPacker< %s, %s >" % (type_to_cpp(t.oftype, proxy = proxy), t.id)
    elif isinstance(t, compiler.TSet):
        return "SetPacker< %s, %s >" % (type_to_cpp(t.oftype, proxy = proxy), t.id)
    elif isinstance(t, compiler.TMap):
        return "MapPacker< %s, %s, %s >" % (type_to_cpp(t.keytype, proxy = proxy), 
            type_to_cpp(t.valtype, proxy = proxy), t.id)
    elif isinstance(t, (compiler.Enum, compiler.Record, compiler.Exception)):
        return "_%sPacker" % (t.name,)
    elif isinstance(t, compiler.Class):
        if proxy:
            return "ObjrefPacker< _%s, %s >" % (type_to_cpp(t, shared = False, proxy = True), t.id)
        else:
            return "ObjrefPacker< %s, %s >" % (type_to_cpp(t, shared = False), t.id)
    else:
        assert False

def const_to_cpp(typ, val):
    if val is None:
        return "null"
    elif typ == compiler.t_bool:
        if val:
            return "true"
        else:
            return "false"
    elif typ == compiler.t_int8:
        return str(val)
    elif typ == compiler.t_int16:
        return str(val)
    elif typ == compiler.t_int32:
        return str(val) + "l"
    elif typ == compiler.t_int64:
        return str(val) + "ll"
    elif typ == compiler.t_float:
        return str(val)
    elif typ == compiler.t_string:
        escaped = "".join("\\%02x" % (ord(ch),) if ord(ch) < 32 or ord(ch) >= 127 else 
            ("\\\\" if ch == "\\" else ('\\"' if ch == '"' else ch)) 
                for ch in val)
        return '"%s"' % (escaped,) 
    else:
        raise IDLError("%r cannot be converted to a C++ const" % (val,))


class CPPTarget(TargetBase):
    from ..langs import cpp
    LANGUAGE = cpp
    
    @contextmanager
    def multinamespace(self, module, *parts):
        parts = ".".join(parts).split(".")
        text = " ".join("namespace %s {" % (p,) for p in parts)
        with module.block(text, prefix = "", suffix = "}" * len(parts)):
            yield
    
    def generate(self, service):
        with self.new_module("%s_server_bindings.hpp" % (service.name,)) as module:
            self.generate_server_header(module, service)
        with self.new_module("%s_server_bindings.cpp" % (service.name,)) as module:
            self.generate_server_module(module, service)
        with self.new_module("%s_client_bindings.hpp" % (service.name,)) as module:
            self.generate_client_header(module, service)
        with self.new_module("%s_client_bindings.cpp" % (service.name,)) as module:
            self.generate_client_module(module, service)
        with self.new_module("%s_server_stub.cpp" % (service.name,)) as module:
            self.generate_server_stub(module, service)
    
    ##########################################################################
    
    def generate_header_signature(self, module, service):
        STMT = module.stmt
        SEP = module.sep
        
        STMT("using namespace agnos")
        STMT("using namespace agnos::packers")
        STMT("using namespace agnos::protocol")
        STMT("using agnos::transports::ITransport")
        SEP()
        STMT('extern const string AGNOS_VERSION')
        STMT('extern const string IDL_MAGIC')
        STMT('extern const vector<string> SUPPORTED_VERSIONS')
    
    def generate_server_header(self, module, service):
        BLOCK = module.block
        STMT = module.stmt
        SEP = module.sep
        DOC = module.doc

        STMT("#ifndef {0}_SERVER_BINDINGS_INCLUDED", service.name)
        STMT("#define {0}_SERVER_BINDINGS_INCLUDED", service.name)
        STMT("#include <agnos.hpp>")
        SEP()
        with self.multinamespace(module, service.package, "ServerBindings"):
            self.generate_header_signature(module, service)
            SEP()
            
            for tp in service.records():
                STMT("class {0}", type_to_cpp(tp))
            for tp in service.classes():
                STMT("class {0}", type_to_cpp(tp, shared = False))
            SEP()
            
            DOC("enums", spacer = True)
            for enum in service.enums():
                self.generate_header_enum(module, enum)
                SEP()

            DOC("records", spacer = True)
            for rec in service.records():
                self.generate_header_record(module, rec, proxy = False)
                SEP()

            DOC("consts", spacer = True)
            for member in service.consts.values():
                STMT("extern const {0} {1}", type_to_cpp(member.type), member.fullname)
            SEP()

            DOC("classes", spacer = True)
            for cls in service.classes():
                self.generate_header_class_interface(module, cls)
                SEP()

            DOC("server implementation", spacer = True)
            self.generate_header_handler_interface(module, service)
            SEP()
            
            self.generate_header_processor_factory(module, service)
            SEP()
            
            DOC("$$extend-main$$")
            SEP()
            
        SEP()
        STMT("#endif // {0}_SERVER_BINDINGS_INCLUDED", service.name)

    def generate_header_enum(self, module, enum):
        BLOCK = module.block
        STMT = module.stmt
        SEP = module.sep

        with BLOCK("enum {0}", enum.name):
            for mem in enum.members[:-1]:
                STMT("{0} = {1}", mem.name, mem.value, suffix = ",")
            STMT("{0} = {1}", enum.members[-1].name, enum.members[-1].value, suffix = "")

    def generate_header_record(self, module, rec, proxy):
        BLOCK = module.block
        STMT = module.stmt
        SEP = module.sep
        if isinstance(rec, compiler.Exception):
            with BLOCK("class {0} : public PackedException", rec.name):
                STMT("public:")
                for mem in rec.members:
                    STMT("{0} {1}", type_to_cpp(mem.type, proxy = proxy), mem.name)
                SEP()
                with BLOCK("{0}()", rec.name):
                    pass
                if rec.members:
                    args = ", ".join("%s %s" % (type_to_cpp(mem.type, proxy = proxy, arg = True), mem.name) 
                        for mem in rec.members)
                    init = ", ".join("%s(%s)" % (mem.name, mem.name) for mem in rec.members)
                    with BLOCK("{0}({1}) : {2}", rec.name, args, init):
                        pass
                with BLOCK("~{0}() throw()", rec.name):
                    pass
                with BLOCK("virtual const char* what() const throw ()"):
                    STMT('return "{0}"', rec.name) 
        else:
            with BLOCK("class {0}", rec.name):
                STMT("public:")
                for mem in rec.members:
                    STMT("{0} {1}", type_to_cpp(mem.type, proxy = proxy), mem.name)
                SEP()
                with BLOCK("{0}()", rec.name):
                    pass
                if rec.members:
                    args = ", ".join("%s %s" % (type_to_cpp(mem.type, proxy = proxy, arg = True), mem.name) 
                        for mem in rec.members)
                    init = ", ".join("%s(%s)" % (mem.name, mem.name) for mem in rec.members)
                    with BLOCK("{0}({1}) : {2}", rec.name, args, init):
                        pass
        SEP()

    def generate_header_class_interface(self, module, cls):
        BLOCK = module.block
        STMT = module.stmt
        SEP = module.sep
        DOC = module.doc
        
        if cls.extends:
            extends = " : " + ", ".join("public I%s" % (c.name,) for c in cls.extends)
        else:
            extends = ""

        with BLOCK("class I{0}{1}", cls.name, extends):
            STMT("public:")
            if cls.attrs:
                DOC("attributes")
            for attr in cls.attrs:
                if attr.get:
                    STMT("virtual {0} get_{1}() = 0", type_to_cpp(attr.type, ret = True), attr.name)
                if attr.set:
                    STMT("virtual void set_{0}({1} value) = 0", attr.name, type_to_cpp(attr.type, arg = True))
            SEP()
            if cls.methods:
                DOC("methods")
            for method in cls.methods:
                args = ", ".join("%s %s" % (type_to_cpp(arg.type, arg = True), arg.name) 
                    for arg in method.args)
                STMT("virtual {0} {1}({2}) = 0", type_to_cpp(method.type, ret = True), method.name, args)
    
    def generate_header_handler_interface(self, module, service):
        BLOCK = module.block
        STMT = module.stmt
        SEP = module.sep
        DOC = module.doc

        with BLOCK("class IHandler"):
            STMT("public:")
            for member in service.funcs.values():
                if isinstance(member, compiler.Func):
                    args = ", ".join("%s %s" % (type_to_cpp(arg.type, arg = True), arg.name) 
                        for arg in member.args)
                    STMT("virtual {0} {1}({2}) = 0", type_to_cpp(member.type, ret = True), 
                        member.fullname, args)

    def generate_header_processor_factory(self, module, service):
        BLOCK = module.block
        STMT = module.stmt
        SEP = module.sep
        DOC = module.doc
        
        with BLOCK("class ProcessorFactory : public IProcessorFactory"):
            STMT("protected:")
            STMT("shared_ptr<IHandler> handler")
            STMT("public:")
            STMT("ProcessorFactory(shared_ptr<IHandler> handler)")
            STMT("shared_ptr<BaseProcessor> create(shared_ptr<ITransport> transport)")
    
    ############################################################################
    
    def generate_module_signature(self, module, service):
        BLOCK = module.block
        STMT = module.stmt
        SEP = module.sep
        DOC = module.doc

        STMT('const string AGNOS_VERSION = "{0}"', compiler.AGNOS_VERSION)
        STMT('const string IDL_MAGIC = "{0}"', service.digest)
        if service.versions:
            STMT("static string _SUPPORTED_VERSIONS[] = {{ {0} }}", ", ".join('"%s"' % (ver,) for ver in service.versions))
            STMT('const vector<string> SUPPORTED_VERSIONS(_SUPPORTED_VERSIONS, _SUPPORTED_VERSIONS + sizeof(_SUPPORTED_VERSIONS) / sizeof(_SUPPORTED_VERSIONS[0]))')
        else:
            STMT('const vector<string> SUPPORTED_VERSIONS')
    
    def generate_server_module(self, module, service):
        BLOCK = module.block
        STMT = module.stmt
        SEP = module.sep
        DOC = module.doc
            
        STMT('#include "{0}_server_bindings.hpp"', service.name)
        SEP()
        with self.multinamespace(module, service.package, "ServerBindings"):
            self.generate_module_signature(module, service)
            
            DOC("enums", spacer = True)
            for enum in service.enums():
                self.generate_module_enum(module, enum)
                SEP()
            
            DOC("records", spacer = True)
            for rec in service.records(lambda mem: not is_complex_type(mem)):
                self.generate_module_record_cls_and_body(module, rec, static = True, proxy = False)
                SEP()
    
            DOC("consts", spacer = True)
            for member in service.consts.values():
                STMT("const {0} {1} = {2}", type_to_cpp(member.type), 
                    member.fullname, const_to_cpp(member.type, member.value))
            SEP()
            
            DOC("server implementation", spacer = True)
            self.generate_module_processor(module, service)
            SEP()
            self.generate_module_processor_factory(module, service)
            SEP()
            
            DOC("$$extend-main$$")
            SEP()
    
    def generate_module_enum(self, module, enum):
        BLOCK = module.block
        STMT = module.stmt
        SEP = module.sep
        
        with BLOCK("class {0} : public IPacker", type_to_packer_type(enum), suffix = "} %s;" % (type_to_packer(enum),)):
            STMT("public:")
            STMT("RECORD_PACKER_IMPL({0}, {1})", enum.name, enum.id)
            SEP()
            with BLOCK("void pack(const data_type& obj, ITransport& transport) const"):
                STMT("{0}.pack((int32_t)obj, transport)", type_to_packer(compiler.t_int32))
            with BLOCK("void unpack(data_type& obj, ITransport& transport) const"):
                STMT("int32_t tmp")
                STMT("{0}.unpack(tmp, transport)", type_to_packer(compiler.t_int32))
                STMT("obj = ({0})tmp", enum.name)

    def generate_module_record_cls_and_body(self, module, rec, static, proxy):
        BLOCK = module.block
        STMT = module.stmt
        SEP = module.sep

        with BLOCK("class {0} : public IPacker", type_to_packer_type(rec), suffix = "} %s;" % (type_to_packer(rec),)):
            if not static:
                STMT("protected:")
                complicated_types = rec.get_complicated_types()
                for tp in complicated_types:
                    STMT("const {0}& {1}", type_to_packer_type(tp, proxy = proxy), type_to_packer(tp))
                args =  ", ".join("const %s& %s" % (type_to_packer_type(tp, proxy = proxy), type_to_packer(tp)) 
                    for tp in complicated_types)
                argsinit = ", ".join("%s(%s)" % (type_to_packer(tp), type_to_packer(tp)) 
                    for tp in complicated_types)
                STMT("public:")
                with BLOCK("_{0}Packer({1}) : {2}", rec.name, args, argsinit):
                    pass
                SEP()
            else:
                STMT("public:")

            STMT("RECORD_PACKER_IMPL({0}, {1})", rec.name, rec.id)
            SEP()

            with BLOCK("void pack(const data_type& obj, ITransport& transport) const"):
                for mem in rec.members:
                    STMT("{0}.pack(obj.{1}, transport)", type_to_packer(mem.type), mem.name)
            
            with BLOCK("void unpack(data_type& obj, ITransport& transport) const"):
                for mem in rec.members:
                    STMT("{0}.unpack(obj.{1}, transport)", type_to_packer(mem.type), mem.name) 

    def generate_module_record_cls(self, module, rec, static, proxy):
        BLOCK = module.block
        STMT = module.stmt
        SEP = module.sep

        with BLOCK("class {0} : public IPacker", type_to_packer_type(rec), suffix = "} %s;" % (type_to_packer(rec),)):
            if not static:
                STMT("protected:")
                complicated_types = rec.get_complicated_types()
                for tp in complicated_types:
                    STMT("const {0}& {1}", type_to_packer_type(tp, proxy = proxy), type_to_packer(tp))
                args =  ", ".join("const %s& %s" % (type_to_packer_type(tp, proxy = proxy), type_to_packer(tp)) 
                    for tp in complicated_types)
                argsinit = ", ".join("%s(%s)" % (type_to_packer(tp), type_to_packer(tp)) 
                    for tp in complicated_types)
                STMT("public:")
                with BLOCK("_{0}Packer({1}) : {2}", rec.name, args, argsinit):
                    pass
                SEP()
            else:
                STMT("public:")

            STMT("RECORD_PACKER_IMPL({0}, {1})", rec.name, rec.id)
            SEP()

            STMT("void pack(const data_type& obj, ITransport& transport) const")
            STMT("void unpack(data_type& obj, ITransport& transport) const")
    
    def generate_module_record_body(self, module, rec, namespace = None):
        BLOCK = module.block
        STMT = module.stmt
        SEP = module.sep
        
        if namespace:
            ns = "%s::%s" % (namespace, type_to_packer_type(rec))
        else:
            ns = type_to_packer_type(rec)

        with BLOCK("void {0}::pack(const data_type& obj, ITransport& transport) const", ns):
            for mem in rec.members:
                STMT("{0}.pack(obj.{1}, transport)", type_to_packer(mem.type), mem.name)
        
        with BLOCK("void {0}::unpack(data_type& obj, ITransport& transport) const", ns):
            for mem in rec.members:
                STMT("{0}.unpack(obj.{1}, transport)", type_to_packer(mem.type), mem.name) 
   
    
    def generate_module_processor_factory(self, module, service):
        BLOCK = module.block
        STMT = module.stmt
        SEP = module.sep
        DOC = module.doc
        
        with BLOCK("ProcessorFactory::ProcessorFactory(shared_ptr<IHandler> handler) : handler(handler)"):
            pass
        with BLOCK("shared_ptr<BaseProcessor> ProcessorFactory::create(shared_ptr<ITransport> transport)"):
            STMT("return shared_ptr<BaseProcessor>(new Processor(transport, handler))")

    def generate_module_processor(self, module, service):
        BLOCK = module.block
        STMT = module.stmt
        SEP = module.sep
        DOC = module.doc
        
        with BLOCK("class Processor : public BaseProcessor"):
            STMT("protected:")

            SEP()
            for cls in service.classes():
                STMT("{0} {1}", type_to_packer_type(cls), type_to_packer(cls))
            SEP()
            generated_records = []
            for rec in service.records(is_complex_type):
                self.generate_module_record_cls_and_body(module, rec, static = False, proxy = False)
                generated_records.append(rec)
                SEP()
            for tp in service.all_types:
                if isinstance(tp, (compiler.TList, compiler.TSet, compiler.TMap)):
                    STMT("{0} {1}", type_to_packer_type(tp), type_to_packer(tp))
            SEP()
            STMT("HeteroMapPacker _heteromap_packer")
            STMT("shared_ptr<IHandler> handler")
            SEP()
            
            STMT("public:")

            with BLOCK("Processor(shared_ptr<ITransport> transport, shared_ptr<IHandler> handler) :", prefix = "", suffix = ""):
                STMT("BaseProcessor(transport)", suffix = ",")
                for tp in service.all_types:
                    if isinstance(tp, (compiler.TList, compiler.TSet)):
                        STMT("{0}({1})", type_to_packer(tp), type_to_packer(tp.oftype), suffix = ",")
                    elif isinstance(tp, compiler.TMap):
                        STMT("{0}({1}, {2})", type_to_packer(tp), type_to_packer(tp.keytype), 
                            type_to_packer(tp.valtype), suffix = ",")
                for cls in service.classes():
                    STMT("{0}(*this)", type_to_packer(cls), suffix = ",")
                for rec in generated_records:
                    args = ", ".join(type_to_packer(tp) for tp in rec.get_complicated_types())
                    STMT("{0}({1})", type_to_packer(rec), args, suffix = ",")
                STMT("_heteromap_packer(999)", suffix=",")
                STMT("handler(handler)", suffix = "")
                STMT("{", suffix = "")
                for tp in service.ordered_types:
                    STMT("map_put(_heteromap_packer.packers_map, {0}, static_cast<IPacker*>(&{1}))", tp.id, type_to_packer(tp))
                STMT("map_put(_heteromap_packer.packers_map, 999, static_cast<IPacker*>(&_heteromap_packer))")
                STMT("}", suffix = "")
            SEP()

            self.generate_process_getinfo(module, service)
            SEP()
            self.generate_process_invoke(module, service)
            SEP()
            DOC("$$extend-processor$$")
            SEP()


    def generate_process_getinfo(self, module, service):
        BLOCK = module.block
        STMT = module.stmt
        SEP = module.sep
        DOC = module.doc

        with BLOCK("void process_get_general_info(HeteroMap& map)"):
            STMT('map.put("AGNOS_VERSION", AGNOS_VERSION)')
            STMT('map.put("IDL_MAGIC", IDL_MAGIC)')
            STMT('map.put("SERVICE_NAME", "{0}")', service.name)
            STMT('map.put("SUPPORTED_VERSIONS", string_packer, SUPPORTED_VERSIONS, list_of_string_packer)')
        SEP()
        with BLOCK("void process_get_functions_info(HeteroMap& map)"):
            STMT("HeteroMap funcinfo")
            STMT("std::map<string, string> args")
            for func in service.funcs.values():
                STMT("funcinfo.clear()")
                STMT("args.clear()")
                STMT('funcinfo.put("name", "{0}")', func.name)
                STMT('funcinfo.put("type", "{0}")', str(func.type))
                for arg in func.args:
                    STMT('args["{0}"] = "{1}"', arg.name, str(arg.type))
                STMT('funcinfo.put("args", string_packer, args, map_of_string_string_packer)')
                STMT('map.put({0}, int32_packer, funcinfo, builtin_heteromap_packer)', func.id)
                SEP()
        SEP()
        with BLOCK("void process_get_function_codes(HeteroMap& map)"):
            for func in service.funcs.values():
                STMT('map.put("{0}", {1})', func.name, func.id)
            
    def generate_process_invoke(self, module, service):
        BLOCK = module.block
        STMT = module.stmt
        SEP = module.sep
        
        with BLOCK("void process_invoke(int32_t seq)"):
            STMT("IPacker * packer = NULL")
            STMT("any result")
            STMT("vector<any> args")
            STMT("any current")
            STMT("int32_t funcid;")
            STMT("{0}.unpack(funcid, *transport)", type_to_packer(compiler.t_int32))
            
            with BLOCK("try") if service.exceptions() else NOOP:
                with BLOCK("switch (funcid)"):
                    for func in service.funcs.values():
                        with BLOCK("case {0}:", func.id):
                            self.generate_invocation_case(module, func)
                            if func.type != compiler.t_void:
                                STMT("packer = static_cast<IPacker*>(&{0})", type_to_packer(func.type))
                            STMT("break")
                    with BLOCK("default:", prefix = None, suffix = None):
                        STMT('throw ProtocolError("unknown function id: ")')
                SEP()
                STMT("{0}.pack(REPLY_SUCCESS, *transport)", type_to_packer(compiler.t_int8))
                with BLOCK("if (packer != NULL)"):
                    STMT("packer->pack_any(result, *transport)")
            
            for tp in service.exceptions():
                with BLOCK("catch ({0}& ex)", tp.name):
                    STMT('DEBUG_LOG("got packed exception: {0}")', tp.name)
                    STMT("transport->reset()")
                    STMT("{0}.pack(REPLY_PACKED_EXCEPTION, *transport)", 
                        type_to_packer(compiler.t_int8))
                    STMT("{0}.pack({1}, *transport)", type_to_packer(compiler.t_int32), tp.id)
                    STMT("{0}.pack(ex, *transport)", type_to_packer(tp))
    
    def generate_invocation_case(self, module, func):
        BLOCK = module.block
        STMT = module.stmt
        SEP = module.sep
        
        if isinstance(func, compiler.Func):
            if func.args:
                for arg in func.args:
                    STMT("current = {0}.unpack_any(*transport)", type_to_packer(arg.type))
                    STMT("args.push_back(current.empty() ? {0}() : current)", type_to_cpp(arg.type))
            callargs = ", ".join("any_cast< %s >(args[%s])" % (type_to_cpp(arg.type), i) 
                for i, arg in enumerate(func.args))
            if func.type == compiler.t_void:
                invocation = "handler->%s(%s)" % (func.fullname, callargs) 
            else:
                invocation = "result = handler->%s(%s)" % (func.fullname, callargs)
        else:
            insttype = func.args[0].type
            STMT("{0} inst", type_to_cpp(insttype));
            STMT("{0}.unpack(inst, *transport)", type_to_packer(insttype))
            
            for arg in func.args[1:]:
                    STMT("current = {0}.unpack_any(*transport)", type_to_packer(arg.type))
                    STMT("args.push_back(current.empty() ? {0}() : current)", type_to_cpp(arg.type))
            
            callargs = ", ".join("any_cast< %s >(args[%s])" % (type_to_cpp(arg.type), i) 
                for i, arg in enumerate(func.args[1:]))
            
            if isinstance(func.origin, compiler.ClassAttr):
                if func.type == compiler.t_void:
                    invocation = "inst->set_%s(any_cast< %s >(args[0]))" % (func.origin.name, 
                        type_to_cpp(func.origin.type))
                else:
                    invocation = "result = inst->get_%s()" % (func.origin.name,)
            else:
                if func.type == compiler.t_void:
                    invocation = "inst->%s(%s)" % (func.origin.name, callargs)
                else:
                    invocation = "result = inst->%s(%s)" % (func.origin.name, callargs)

        with BLOCK("try {0}", "{", prefix = ""):
            STMT(invocation)
        with BLOCK("catch (PackedException& ex) {0}", "{", prefix = ""):
            STMT("throw")
        with BLOCK("catch (std::exception& ex) {0}", "{", prefix = ""):
            STMT('throw GenericException(ex.what(), "<no info>")')
        
    ############################################################################
    
    def generate_client_header(self, module, service):
        BLOCK = module.block
        STMT = module.stmt
        SEP = module.sep
        DOC = module.doc

        STMT("#ifndef {0}_CLIENT_BINDINGS_INCLUDED", service.name)
        STMT("#define {0}_CLIENT_BINDINGS_INCLUDED", service.name)
        STMT("#include <sstream>")
        STMT("#include <agnos.hpp>")
        SEP()
        with self.multinamespace(module, service.package, "ClientBindings"):
            self.generate_header_signature(module, service)
            SEP()
            
            for tp in service.records():
                STMT("class {0}", type_to_cpp(tp, proxy = True))
            for tp in service.classes():
                STMT("class _{0}", type_to_cpp(tp, proxy = True))
                STMT("typedef shared_ptr< _{0} > {0}", type_to_cpp(tp, proxy = True))
            SEP()
            
            DOC("enums", spacer = True)
            for enum in service.enums():
                self.generate_header_enum(module, enum)
                SEP()

            DOC("records", spacer = True)
            for rec in service.records():
                self.generate_header_record(module, rec, proxy = True)
                SEP()

            DOC("consts", spacer = True)
            for member in service.consts.values():
                STMT("extern const {0} {1}", type_to_cpp(member.type), member.fullname)
            SEP()

            DOC("classes", spacer = True)
            self.generate_header_base_proxy(module, service)
            SEP()
            for cls in service.classes():
                self.generate_header_class_proxy(module, cls)
                SEP()

            DOC("client implementation", spacer = True)
            self.generate_header_client(module, service)
            SEP()

            DOC("$$extend-main$$")
            SEP()
            
        SEP()
        STMT("#endif // {0}_CLIENT_BINDINGS_INCLUDED", service.name)        

    def generate_header_base_proxy(self, module, service):
        BLOCK = module.block
        STMT = module.stmt
        SEP = module.sep
        DOC = module.doc
        
        STMT("class Client")
        STMT("template<typename T> class ProxySerializer")
        SEP()
        with BLOCK("class BaseProxy"):
            STMT("protected:")
            STMT("template<typename T> friend class ProxySerializer")
            STMT("friend class protocol::ClientUtils")
            STMT("Client& _client")
            STMT("objref_t _oid")
            STMT("bool _disposed")
            STMT("friend std::ostream& operator<< (std::ostream& stream, const BaseProxy& proxy)")
            SEP()
            STMT("public:")
            with BLOCK("BaseProxy(Client& client, objref_t oid, bool owns_ref) : _client(client), _oid(oid)"):
                STMT("_disposed = owns_ref ? false : true")
            with BLOCK("~BaseProxy()"):
                STMT("dispose()")
            STMT("void dispose()")

    def generate_header_class_proxy(self, module, cls):
        BLOCK = module.block
        STMT = module.stmt
        SEP = module.sep
        DOC = module.doc
        
        #STMT("class _{0}Proxy", cls.name)
        
        with BLOCK("class _{0}Proxy : public BaseProxy", cls.name):
            STMT("public:")
            STMT("_{0}Proxy(Client& client, objref_t oid, bool owns_ref)", cls.name)
            for attr in cls.all_attrs:
                if attr.get:
                    STMT("{0} get_{1}()", type_to_cpp(attr.type, proxy = True, ret = True), attr.name)
                if attr.set:
                    STMT("void set_{0}({1} value)", attr.name, type_to_cpp(attr.type, proxy = True, arg = True))
            SEP()
            for method in cls.all_methods:
                if not method.clientside:
                    continue
                args = ", ".join("%s %s" % (type_to_cpp(arg.type, proxy = True, arg = True), arg.name) 
                    for arg in method.args)
                STMT("{0} {1}({2})", type_to_cpp(method.type, proxy = True, ret = True), method.name, args)
            if cls.all_derived:
                SEP()
                DOC("downcasts")
                for cls2 in cls.all_derived:
                    STMT("{0} cast_to_{1}()", type_to_cpp(cls2, proxy = True), cls2.name)
            if cls.all_bases:
                SEP()
                DOC("upcasts")
                for cls2 in cls.all_bases:
                    STMT("{0} cast_to_{1}()", type_to_cpp(cls2, proxy = True), cls2.name)
    
    def generate_header_client(self, module, service):
        BLOCK = module.block
        STMT = module.stmt
        SEP = module.sep
        DOC = module.doc
        
        self.generate_header_client_proxy_serializer(module, service)
        SEP()
        self.generate_header_client_internal_functions(module, service)
        SEP()
        with BLOCK("class Client : public BaseClient"):
            STMT("protected:")
            STMT("friend class _Functions")
            SEP()
            for cls in service.classes():
                STMT("{0} {1}", type_to_packer_type(cls, proxy = True), type_to_packer(cls))
            SEP()
            for rec in service.records(is_complex_type):
                self.generate_module_record_cls(module, rec, static = False, proxy = True)
                SEP()
            for tp in service.all_types:
                if isinstance(tp, (compiler.TList, compiler.TSet, compiler.TMap)):
                    STMT("{0} {1}", type_to_packer_type(tp, proxy = True), type_to_packer(tp))
            SEP()
            STMT("HeteroMapPacker _heteromap_packer")
            SEP()
            for cls in service.classes():
                STMT("ProxySerializer<_{0}Proxy> _{0}_proxy_serializer", cls.name)
            SEP()
            STMT("public:")
            STMT("_Functions _funcs")
            SEP()
            STMT("Client(shared_ptr<ITransport> transport)")
            SEP()
            self.namespaces = self.generate_client_namespaces(module, service)
            SEP()
            self.generate_header_client_funcs(module, service)
            SEP()
            self.generate_header_client_helpers(module, service)
        SEP()
        self.generate_header_client_factories(module, service)

    def generate_header_client_proxy_serializer(self, module, service):
        BLOCK = module.block
        STMT = module.stmt
        SEP = module.sep

        with BLOCK("template<typename T> class ProxySerializer : public ISerializer", suffix = "};"):
            STMT("protected:")
            STMT("Client& client")
            SEP()
            STMT("public:")
            STMT("ProxySerializer(Client& client)")
            STMT("objref_t store(objref_t oid, any obj)")
            STMT("any load(objref_t oid)")
    
    def generate_header_client_internal_functions(self, module, service):
        BLOCK = module.block
        STMT = module.stmt
        SEP = module.sep
        
        with BLOCK("class _Functions"):
            STMT("protected:")
            STMT("Client& client")
            SEP()
            STMT("public:")
            STMT("_Functions(Client& client)")
            SEP()
            for func in service.funcs.values():
                if isinstance(func, compiler.Func):
                    args = ", ".join("%s %s" % (type_to_cpp(arg.type, proxy = True, arg = True), arg.name) 
                        for arg in func.args)
                else:
                    args = ["objref_t _oid"]
                    args.extend("%s %s" % (type_to_cpp(arg.type, proxy = True, arg = True), arg.name) 
                        for arg in func.args[1:])
                    args = ", ".join(args)                
                STMT("{0} sync_{1}({2})", type_to_cpp(func.type, proxy = True, ret = True), func.id, args)

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
        with BLOCK("class _Namespace{0}", root["__id__"]):
            subnamespaces = []
            STMT("protected:")
            STMT("_Functions& _funcs")
            SEP()
            STMT("public:")
            for name, node in root.iteritems():
                if isinstance(node, dict):
                    self.generate_client_namespace_classes(module, node)
                    subnamespaces.append((name, node["__id__"]))
                elif isinstance(node, compiler.Func):
                    func = node
                    args = ", ".join("%s %s" % (type_to_cpp(arg.type, proxy = True, arg = True), arg.name) 
                        for arg in func.args)
                    callargs = ", ".join(arg.name for arg in func.args)
                    with BLOCK("{0} {1}({2})", type_to_cpp(func.type, proxy = True, ret = True), func.name, args):
                        if func.type == compiler.t_void:
                            STMT("_funcs.sync_{0}({1})", func.id, callargs)
                        else:
                            STMT("return _funcs.sync_{0}({1})", func.id, callargs)
                elif isinstance(node, compiler.Const):
                    STMT("static const {0} {1} = {2}", type_to_cpp(node.type), 
                        node.name, const_to_cpp(node.type, node.value))
                else:
                    pass
            SEP()
            with BLOCK("_Namespace{0}(_Functions& funcs) :", root["__id__"], prefix = "", suffix = ""): 
                for name, id in subnamespaces:
                    STMT("{0}(_Namespace{1}(funcs))", name, id, suffix = ",")
                STMT("_funcs(funcs)", suffix = "")
                STMT("{}", suffix = "")
        STMT("_Namespace{0} {1}", root["__id__"], root["__name__"])

    def generate_header_client_funcs(self, module, service):
        BLOCK = module.block
        STMT = module.stmt
        SEP = module.sep
        DOC = module.doc
        
        for func in service.funcs.values():
            if not isinstance(func, compiler.Func) or func.namespace or not func.clientside:
                continue
            args = ", ".join("%s %s" % (type_to_cpp(arg.type, proxy = True, arg = True), arg.name) 
                for arg in func.args)
            callargs = ", ".join(arg.name for arg in func.args)
            STMT("{0} {1}({2})", type_to_cpp(func.type, proxy = True, ret = True), func.name, args)

    def generate_header_client_helpers(self, module, service):
        BLOCK = module.block
        STMT = module.stmt
        SEP = module.sep
        
        STMT("void assert_service_compatibility()")

    def generate_header_client_factories(self, module, service):
        BLOCK = module.block
        STMT = module.stmt
        SEP = module.sep
        with BLOCK("class SocketClient : public Client"):
            STMT("public:")
            STMT("SocketClient(shared_ptr<transports::SocketTransport> trns)")
            STMT("SocketClient(const string& host, unsigned short port)")
            STMT("SocketClient(const string& host, const string& port)")
        SEP()
        with BLOCK("class URLClient : public Client"):
            STMT("public:")
            STMT("URLClient(const string& url)")
        SEP()
        STMT("#ifdef BOOST_PROCESS_SUPPORTED")
        with BLOCK("class SubprocClient : public Client"):
            STMT("public:")
            STMT("SubprocClient(const string& executable)")
            STMT("SubprocClient(const string& executable, const vector<string>& args)")
        STMT("#endif // ifdef BOOST_PROCESS_SUPPORTED")

    
    ############################################################################
    
    def generate_client_module(self, module, service):
        BLOCK = module.block
        STMT = module.stmt
        SEP = module.sep
        DOC = module.doc

        STMT('#include "{0}_client_bindings.hpp"', service.name)
        SEP()
        with self.multinamespace(module, service.package, "ClientBindings"):
            self.generate_module_signature(module, service)
            SEP()
            
            DOC("enums", spacer = True)
            for enum in service.enums():
                self.generate_module_enum(module, enum)
                SEP()
            
            DOC("records", spacer = True)
            for rec in service.records(lambda mem: not is_complex_type(mem)):
                self.generate_module_record_cls_and_body(module, rec, static = True, proxy = False)
                SEP()
    
            DOC("consts", spacer = True)
            for member in service.consts.values():
                STMT("const {0} {1} = {2}", type_to_cpp(member.type), 
                    member.fullname, const_to_cpp(member.type, member.value))
            SEP()
            
            DOC("classes", spacer = True)
            self.generate_module_base_proxy(module, service)
            SEP()
            for cls in service.classes():
                self.generate_module_class_proxy(module, cls)
                SEP()
            
            DOC("client implementation", spacer = True)
            self.generate_module_client(module, service)
            SEP()
            self.generate_module_client_factories(module, service)
            SEP()
            
            DOC("$$extend-main$$")
            SEP()

    def generate_module_client_proxy_serializer(self, module, service):
        BLOCK = module.block
        STMT = module.stmt
        SEP = module.sep

        with BLOCK("template<typename T> ProxySerializer<T>::ProxySerializer(Client& client) : client(client)"):
            pass
        SEP()
        with BLOCK("template<typename T> objref_t ProxySerializer<T>::store(objref_t oid, any obj)"):
            with BLOCK("if (obj.empty())"):
                STMT("return -1")
            STMT("shared_ptr<BaseProxy> proxy = *boost::unsafe_any_cast<shared_ptr<BaseProxy> >(&obj)")
            with BLOCK("if (!proxy)"):
                STMT("return -1")
            STMT("return proxy->_oid")
        
        SEP()
        with BLOCK("template<typename T> any ProxySerializer<T>::load(objref_t oid)"):
            with BLOCK("if (oid < 0)"):
                STMT("return any(shared_ptr<T>())")
            STMT("shared_ptr<T> proxy = client._utils.get_proxy<T>(oid)")
            with BLOCK("if (proxy.get() == NULL)"):
                STMT("proxy = shared_ptr<T>(new T(client, oid, true))")
                STMT("client._utils.cache_proxy(proxy)")
            STMT("return proxy")

    def generate_module_base_proxy(self, module, service):
        BLOCK = module.block
        STMT = module.stmt
        SEP = module.sep
        DOC = module.doc
        
        with BLOCK("void BaseProxy::dispose()"):
            with BLOCK("if (_disposed)"):
                STMT("return")
            STMT("_disposed = true")
            STMT("_client._utils.decref(_oid)")
        
        with BLOCK("std::ostream& operator<< (std::ostream& stream, const BaseProxy& proxy)"):
            STMT('stream << "<Proxy@" << proxy._oid << ">"')
            STMT("return stream")

    def generate_module_class_proxy(self, module, cls):
        BLOCK = module.block
        STMT = module.stmt
        SEP = module.sep
        DOC = module.doc
        
        with BLOCK("_{0}Proxy::_{0}Proxy(Client& client, objref_t oid, bool owns_ref) : BaseProxy(client, oid, owns_ref)", cls.name):
            pass
        SEP()
        for attr in cls.all_attrs:
            if attr.get:
                with BLOCK("{1} _{0}Proxy::get_{2}()", cls.name, 
                        type_to_cpp(attr.type, proxy = True, ret = True), attr.name):
                    STMT("return _client._funcs.sync_{0}(_oid)", attr.getter.id)
            if attr.set:
                with BLOCK("void _{0}Proxy::set_{1}({2} value)", cls.name, attr.name, 
                        type_to_cpp(attr.type, proxy = True, arg = True)):
                    STMT("_client._funcs.sync_{0}(_oid, value)", attr.setter.id)
        SEP()
        for method in cls.all_methods:
            if not method.clientside:
                continue
            args = ", ".join("%s %s" % (type_to_cpp(arg.type, proxy = True, arg = True), arg.name) 
                for arg in method.args)
            with BLOCK("{0} _{1}Proxy::{2}({3})", type_to_cpp(method.type, proxy = True, ret = True), cls.name, method.name, args):
                callargs = ["_oid"] + [arg.name for arg in method.args]
                if method.type == compiler.t_void:
                    STMT("_client._funcs.sync_{0}({1})", method.func.id, ", ".join(callargs))
                else:
                    STMT("return _client._funcs.sync_{0}({1})", method.func.id, ", ".join(callargs))
        if cls.all_derived:
            for cls2 in cls.all_derived:
                with BLOCK("{0} _{1}Proxy::cast_to_{2}()", type_to_cpp(cls2, proxy = True), cls.name, cls2.name):
                    STMT("return shared_ptr<_{0}Proxy>(new _{0}Proxy(_client, _oid, false))", cls2.name)
        if cls.all_bases:
            for cls2 in cls.all_bases:
                with BLOCK("{0} _{1}Proxy::cast_to_{2}()", type_to_cpp(cls2, proxy = True), cls.name, cls2.name):
                    STMT("return shared_ptr<_{0}Proxy>(new _{0}Proxy(_client, _oid, false))", cls2.name)
    
    def generate_module_client(self, module, service):
        BLOCK = module.block
        STMT = module.stmt
        SEP = module.sep
        DOC = module.doc

        self.generate_module_client_proxy_serializer(module, service)
        SEP()
        self.generate_module_client_internal_functions(module, service)
        SEP()
        for rec in service.records(is_complex_type):
            self.generate_module_record_body(module, rec, "Client")
        SEP()
        with BLOCK("Client::Client(shared_ptr<ITransport> transport) :", prefix = "", suffix = ""):
            STMT("BaseClient(transport)", suffix = ",")
            STMT("_funcs(*this)", suffix=",")
            for tp in service.all_types:
                if isinstance(tp, (compiler.TList, compiler.TSet)):
                    STMT("{0}({1})", type_to_packer(tp), type_to_packer(tp.oftype), suffix = ",")
                elif isinstance(tp, compiler.TMap):
                    STMT("{0}({1}, {2})", type_to_packer(tp), type_to_packer(tp.keytype), 
                        type_to_packer(tp.valtype), suffix = ",")
            for cls in service.classes():
                STMT("_{0}_proxy_serializer(*this)", cls.name, suffix=",")
                STMT("{0}(_{1}_proxy_serializer)", type_to_packer(cls), cls.name, suffix = ",")
            for rec in service.records(is_complex_type):
                args = ", ".join(type_to_packer(tp) for tp in rec.get_complicated_types())
                STMT("{0}({1})", type_to_packer(rec), args, suffix = ",")
            for name, id in self.namespaces:
                STMT("{0}(_funcs)", name, suffix = ",")
            STMT("_heteromap_packer(999)", suffix="")
            STMT("{", suffix = "")
            for tp in service.ordered_types:
                STMT("map_put(_heteromap_packer.packers_map, {0}, static_cast<IPacker*>(&{1}))", tp.id, type_to_packer(tp))
            STMT("map_put(_heteromap_packer.packers_map, 999, static_cast<IPacker*>(&_heteromap_packer))")
            SEP()
            for exc in service.exceptions():
                STMT("map_put(_utils.packed_exceptions_map, {0}, static_cast<IPacker*>(&{1}))", exc.id, type_to_packer(exc))
            SEP()
            STMT("}", suffix = "")
        SEP()
        self.generate_module_client_funcs(module, service)
        SEP()
        self.generate_module_client_helpers(module, service)

    def generate_module_client_internal_functions(self, module, service):
        BLOCK = module.block
        STMT = module.stmt
        SEP = module.sep

        with BLOCK("_Functions::_Functions(Client& client) : client(client)"):
            pass
        SEP()
        
        for func in service.funcs.values():
            if isinstance(func, compiler.Func):
                method = False
                args = ", ".join("%s %s" % (type_to_cpp(arg.type, proxy = True, arg = True), arg.name) 
                    for arg in func.args)
            else:
                method = True
                args = ["objref_t _oid"]
                args.extend("%s %s" % (type_to_cpp(arg.type, proxy = True, arg = True), arg.name) 
                    for arg in func.args[1:])
                args = ", ".join(args)
            with BLOCK("{0} _Functions::sync_{1}({2})", type_to_cpp(func.type, proxy = True, ret = True), 
                    func.id, args):
                if is_complicated_type(func.type):
                    STMT("int seq = client._utils.begin_call({0}, client.{1}, {2})", 
                        func.id, type_to_packer(func.type), is_type_shared_ptr(func.type))
                else:
                    STMT("int seq = client._utils.begin_call({0}, {1}, {2})", func.id, 
                        type_to_packer(func.type), is_type_shared_ptr(func.type))
                if func.args:
                    with BLOCK("try"):
                        if method:
                            STMT("int64_packer.pack(_oid, *client._utils.transport)")
                        for arg in func.args[1:] if method else func.args:
                            if is_complicated_type(arg.type):
                                STMT("client.{0}.pack({1}, *client._utils.transport)", 
                                    type_to_packer(arg.type), arg.name)
                            else:
                                STMT("{0}.pack({1}, *client._utils.transport)", 
                                    type_to_packer(arg.type), arg.name)
                    with BLOCK("catch (std::exception& ex)"):
                        STMT("client._utils.cancel_call()")
                        STMT("throw")
                STMT("client._utils.end_call()")
                if func.type == compiler.t_void:
                    STMT("client._utils.get_reply(seq)")
                else:
                    STMT("return client._utils.get_reply_as< {0} >(seq)", 
                        type_to_cpp(func.type, proxy = True, ret = True))
            SEP()    
    
    def generate_module_client_helpers(self, module, service):
        BLOCK = module.block
        STMT = module.stmt
        SEP = module.sep
        
        with BLOCK("void Client::assert_service_compatibility()"):
            STMT("shared_ptr<HeteroMap> info = get_service_info(INFO_GENERAL)")
            STMT('string agnos_version = info->get_as<string>("AGNOS_VERSION")')
            STMT('string service_name = info->get_as<string>("SERVICE_NAME")')
            
            with BLOCK('if (agnos_version != AGNOS_VERSION)'):
                STMT('''throw WrongAgnosVersion("expected version ")''')
            with BLOCK('if (service_name != "{0}")', service.name):
                STMT('''throw WrongServiceName("expected service '{0}', found '" + service_name + "'")''', service.name)
            if service.clientversion:
                STMT("bool found = false")
                with BLOCK('if (info->contains("SUPPORTED_VERSIONS"))'):
                    STMT('vector<string> supported_versions = info->get_as< vector<string> >("SUPPORTED_VERSIONS")')
                    STMT("vector<string>::const_iterator it")
                    with BLOCK("for (it = supported_versions.begin(); it != supported_versions.end(); it++)"):
                        with BLOCK("if (*it == CLIENT_VERSION)"):
                            STMT("found = true")
                            STMT("break")
                with BLOCK("if (!found)"):
                    STMT('''throw IncompatibleServiceVersion("server does not support client version '{0}'")''', 
                        service.clientversion)

    def generate_module_client_factories(self, module, service):
        BLOCK = module.block
        STMT = module.stmt
        SEP = module.sep
        
        with BLOCK("SocketClient::SocketClient(shared_ptr<transports::SocketTransport> trns) :", prefix = "", suffix = "{}"):
            STMT("Client(trns)", suffix = "")
        with BLOCK("SocketClient::SocketClient(const string& host, unsigned short port) :", prefix = "", suffix = "{}"):
            STMT("Client(shared_ptr<transports::SocketTransport>(new transports::SocketTransport(host, port)))", suffix = "")
        with BLOCK("SocketClient::SocketClient(const string& host, const string& port) :", prefix = "", suffix = "{}"):
            STMT("Client(shared_ptr<transports::SocketTransport>(new transports::SocketTransport(host, port)))", suffix = "")
        SEP()
        STMT("#ifdef BOOST_PROCESS_SUPPORTED")
        with BLOCK("SubprocClient::SubprocClient(const string& executable) :", prefix = "", suffix = "{}"):
            STMT("Client(transports::ProcTransport::connect(executable))", suffix = "")
        with BLOCK("SubprocClient::SubprocClient(const string& executable, const vector<string>& args) :", prefix = "", suffix = "{}"):
            STMT("Client(transports::ProcTransport::connect(executable, args))", suffix = "")
        STMT("#endif // BOOST_PROCESS_SUPPORTED")


    def generate_module_client_funcs(self, module, service):
        BLOCK = module.block
        STMT = module.stmt
        SEP = module.sep
        
        for func in service.funcs.values():
            if not isinstance(func, compiler.Func) or func.namespace or not func.clientside:
                continue
            args = ", ".join("%s %s" % (type_to_cpp(arg.type, proxy = True, arg = True), arg.name) 
                for arg in func.args)
            callargs = ", ".join(arg.name for arg in func.args)
            with BLOCK("{0} Client::{1}({2})", type_to_cpp(func.type, proxy = True, ret = True), 
                    func.name, args):
                if func.type == compiler.t_void:
                    STMT("_funcs.sync_{0}({1})", func.id, callargs)
                else:
                    STMT("return _funcs.sync_{0}({1})", func.id, callargs)
    
    ##########################################################################
    
    def generate_server_stub(self, module, service):
        BLOCK = module.block
        STMT = module.stmt
        SEP = module.sep
        DOC = module.doc
        
        DOC("this is an auto-generated server skeleton", box = True)
        STMT('#include "{0}_server_bindings.hpp"', service.name)
        SEP()
        STMT("using namespace agnos")
        STMT("using namespace {0}::ServerBindings", service.package.replace(".", "::"))
        SEP(2)
        DOC("classes", spacer = True)
        for cls in service.classes():
            with BLOCK("class {0} : public I{0}", cls.name):
                STMT("protected:")
                for attr in cls.all_attrs:
                    STMT("{0} _{1}", type_to_cpp(attr.type, ret = True), attr.name)
                SEP()
                STMT("public:")
                args = ", ".join("%s %s" % (type_to_cpp(attr.type, ret = True), attr.name) for attr in cls.all_attrs)
                if cls.all_attrs:
                    with BLOCK("{0}({1}) :", cls.name, args, prefix = "", suffix = ""):
                        for attr in cls.all_attrs[:-1]:
                            STMT("_{0}({0})", attr.name, suffix = ",")
                        STMT("_{0}({0})", cls.all_attrs[-1].name, suffix = "")
                    STMT("{", suffix=  "")
                    STMT("}", suffix=  "")
                SEP()
                for attr in cls.all_attrs:
                    if attr.get:
                        with BLOCK("{0} get_{1}()", type_to_cpp(attr.type, ret = True), attr.name):
                            STMT("return _{0}", attr.name)
                    if attr.set:
                        with BLOCK("void set_{0}({1} value)", attr.name, type_to_cpp(attr.type, arg = True)):
                            STMT("_{0} = value", attr.name)
                    SEP()
                for method in cls.all_methods:
                    args = ", ".join("%s %s" % (type_to_cpp(arg.type, arg = True), arg.name) 
                        for arg in method.args)
                    with BLOCK("{0} {1}({2})", type_to_cpp(method.type, ret = True), method.name, args):
                        DOC("implement me")
                    SEP()
            SEP()
        DOC("handler", spacer = True)
        with BLOCK("class Handler : public IHandler"):
            STMT("public:")
            for member in service.funcs.values():
                if not isinstance(member, compiler.Func):
                    continue
                args = ", ".join("%s %s" % (type_to_cpp(arg.type, arg = True), arg.name) 
                    for arg in member.args)
                with BLOCK("{0} {1}({2})", type_to_cpp(member.type, ret = True), 
                        member.fullname, args):
                    DOC("implement me")
                SEP()
        SEP()
        DOC("main", spacer = True)
        with BLOCK("int main(int argc, const char * argv[])"):
            STMT("ProcessorFactory processor_factory(shared_ptr<IHandler>(new Handler()))")
            SEP()
            STMT("agnos::servers::CmdlineServer server(processor_factory)")
            STMT("return server.main(argc, argv)")
        SEP()





