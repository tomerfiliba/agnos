##############################################################################
# Part of the Agnos RPC Framework
#    http://agnos.sourceforge.net
#
# Copyright 2010, International Business Machines Corp.
#                 Author: Tomer Filiba (tomerf@il.ibm.com)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
##############################################################################
import itertools
import time
import uuid
import os

from .base import TargetBase, NOOP
from .. import compiler
from ..compiler import is_complex_type


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
    elif t == compiler.t_heteromap:
        return "Agnos.HeteroMap"
    elif isinstance(t, compiler.TList):
        return "IList<%s>" % (type_to_cs(t.oftype, proxy = proxy),)
    elif isinstance(t, compiler.TSet):
        return "ICollection<%s>" % (type_to_cs(t.oftype, proxy = proxy),)
    elif isinstance(t, compiler.TMap):
        return "IDictionary<%s, %s>" % (type_to_cs(t.keytype, proxy = proxy), 
            type_to_cs(t.valtype, proxy = proxy))
    elif isinstance(t, (compiler.Enum, compiler.Record, compiler.Exception)):
        return "%s" % (t.name,)
    elif isinstance(t, compiler.Class):
        if proxy:
            return "%sProxy" % (t.name,)
        else:
            return "I%s" % (t.name,)
    else:
        assert False

def type_to_cs_full(t, service, proxy = False):
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
    elif t == compiler.t_heteromap:
        return "Agnos.HeteroMap"
    elif isinstance(t, compiler.TList):
        return "IList<%s>" % (type_to_cs_full(t.oftype, service),)
    elif isinstance(t, compiler.TSet):
        return "ICollection<%s>" % (type_to_cs_full(t.oftype, service),)
    elif isinstance(t, compiler.TMap):
        return "IDictionary<%s, %s>" % (type_to_cs_full(t.keytype, service), 
            type_to_cs_full(t.valtype, service))
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

def const_to_cs(typ, val):
    if val is None:
        return "null"
    elif typ == compiler.t_bool:
        if val:
            return "true"
        else:
            return "false"
    elif typ == compiler.t_int8:
        return repr(val)
    elif typ == compiler.t_int16:
        return repr(val)
    elif typ == compiler.t_int32:
        return repr(val)
    elif typ == compiler.t_int64:
        return repr(val)
    elif typ == compiler.t_float:
        return repr(val)
    elif typ == compiler.t_string:
        return repr(val)
    #elif isinstance(val, list):
    #    return "$const-list %r" % (val,)
    #    #return "new ArrayList<%s>{{%s}}" % (typ.oftype, body,)
    #elif isinstance(val, dict):
    #    return "$const-map %r " % (val,)
    else:
        raise IDLError("%r cannot be converted to a c# const" % (val,))


class CSharpTarget(TargetBase):
    from ..langs import clike
    LANGUAGE = clike
    
    def generate(self, service):
        service.guid = uuid.uuid1()
        
        with self.new_module("%sBindings.cs" % (service.name,)) as module:
            BLOCK = module.block
            STMT = module.stmt
            SEP = module.sep
            DOC = module.doc
            
            STMT("using System")
            STMT("using System.IO")
            STMT("using System.Net")
            STMT("using System.Net.Sockets")
            STMT("using System.Diagnostics")
            STMT("using System.Collections.Generic")
            STMT("using Agnos")
            STMT("using Agnos.Transports")
            SEP()
            if service.package == service.name:
                service.package2 = service.package + "Bindings"
            else:
                service.package2 = service.package
            with BLOCK("namespace {0}", service.package2):
                #self.generate_shared_bindings(module, service)
                #SEP()
                self.generate_server_bindings(module, service)
                SEP()
                self.generate_client_bindings(module, service)
                SEP()
        
        with self.new_module("%sServerStub.cs" % (service.name,)) as module:
            self.generate_server_stub(module, service)
        
        self.generate_assembly_info(service)

    def generate_server_bindings(self, module, service):
        BLOCK = module.block
        STMT = module.stmt
        SEP = module.sep
        DOC = module.doc
        
        with BLOCK("namespace ServerBindings"):
            with BLOCK("public static partial class {0}", service.name):
                STMT('public const string AGNOS_PROTOCOL_VERSION = "{0}"', compiler.AGNOS_PROTOCOL_VERSION)
                STMT('public const string AGNOS_TOOLCHAIN_VERSION = "{0}"', compiler.AGNOS_TOOLCHAIN_VERSION)
                STMT('public const string IDL_MAGIC = "{0}"', service.digest)
                STMT('public static readonly List<string> SUPPORTED_VERSIONS = new List<string> {{ {0} }}',
                    ", ".join('"%s"' % (ver,) for ver in service.versions))

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
                    STMT("public const {0} {1} = {2}", type_to_cs(member.type), 
                        member.fullname, const_to_cs(member.type, member.value))
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
    
    def generate_client_bindings(self, module, service):
        BLOCK = module.block
        STMT = module.stmt
        SEP = module.sep
        DOC = module.doc
        
        with BLOCK("namespace ClientBindings"):
            with BLOCK("public static partial class {0}", service.name):
                STMT('public const string AGNOS_PROTOCOL_VERSION = "{0}"', compiler.AGNOS_PROTOCOL_VERSION)
                STMT('public const string AGNOS_TOOLCHAIN_VERSION = "{0}"', compiler.AGNOS_TOOLCHAIN_VERSION)
                STMT('public const string IDL_MAGIC = "{0}"', service.digest)
                if not service.clientversion:
                    STMT("public const string CLIENT_VERSION = null")
                else:
                    STMT('public const string CLIENT_VERSION = "{0}"', service.clientversion)

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
                        STMT("public const {0} {1} = {2}", type_to_cs(member.type), 
                            member.name, const_to_cs(member.type, member.value))
                SEP()
                
                DOC("classes", spacer = True)
                self.generate_base_class_proxy(module, service)
                SEP()
                for cls in service.classes():
                    self.generate_class_proxy(module, service, cls)
                    SEP()

                DOC("client", spacer = True)
                self.generate_client(module, service)

    def generate_assembly_info(self, service):
        if os.path.isfile(os.path.join(self.path, "AssemblyInfo.cs")):
            # don't regenerate AssemblyInfo if it already exists
            return
        text = """using System.Reflection;
            using System.Runtime.CompilerServices;
            using System.Runtime.InteropServices;
            
            // General Information about an assembly is controlled through the following 
            // set of attributes. Change these attribute values to modify the information
            // associated with an assembly.
            [assembly: AssemblyTitle("{0} Agnos Bindings")]
            [assembly: AssemblyDescription("The auto-generated Agnos bindings for {0}")]
            [assembly: AssemblyConfiguration("")]
            [assembly: AssemblyCompany("")]
            [assembly: AssemblyProduct("{0}")]
            [assembly: AssemblyCopyright("Copyright {2}")]
            [assembly: AssemblyTrademark("")]
            [assembly: AssemblyCulture("")]
            
            // Setting ComVisible to false makes the types in this assembly not visible 
            // to COM components.  If you need to access a type in this assembly from 
            // COM, set the ComVisible attribute to true on that type.
            [assembly: ComVisible(false)]
            
            // The following GUID is for the ID of the typelib if this project is exposed to COM
            [assembly: Guid("{1}")]
            
            // Version information for an assembly consists of the following four values:
            //
            //      Major Version
            //      Minor Version 
            //      Build Number
            //      Revision
            //
            // You can specify all the values or you can default the Build and Revision Numbers 
            // by using the '*' as shown below:
            // [assembly: AssemblyVersion("1.0.*")]
            [assembly: AssemblyVersion("1.0.0.0")]
            [assembly: AssemblyFileVersion("1.0.0.0")]
            """.format(service.name, service.guid, time.gmtime().tm_year)
        with self.open("AssemblyInfo.cs") as f:
            text2 = "\n".join(l.lstrip() for l in text.splitlines())
            f.write(text2)

    def _generate_templated_packer_for_type(self, tp, proxy):
        if isinstance(tp, compiler.TList):
            return "new Packers.ListOf<%s>(%s, %s)" % (type_to_cs(tp.oftype, proxy = proxy), 
                tp.id, self._generate_templated_packer_for_type(tp.oftype, proxy = proxy))
        elif isinstance(tp, compiler.TSet):
            return "new Packers.SetOf<%s>(%s, %s)" % (type_to_cs(tp.oftype, proxy = proxy), 
                tp.id, self._generate_templated_packer_for_type(tp.oftype, proxy = proxy))
        elif isinstance(tp, compiler.TMap):
            return "new Packers.MapOf<%s, %s>(%s, %s, %s)" % (
                type_to_cs(tp.keytype, proxy = proxy), 
                type_to_cs(tp.valtype, proxy = proxy), 
                tp.id, 
                self._generate_templated_packer_for_type(tp.keytype, proxy = proxy),
                self._generate_templated_packer_for_type(tp.valtype, proxy = proxy))
        else:
            return type_to_packer(tp)

    def generate_templated_packers_decl(self, module, service, proxy):
        BLOCK = module.block
        STMT = module.stmt
        SEP = module.sep
        
        for tp in service.all_types:
            if isinstance(tp, (compiler.TList, compiler.TSet, compiler.TMap)):
                if is_complex_type(tp):
                    STMT("internal readonly Packers.AbstractPacker _{0}", tp.stringify())
                else:
                    definition = self._generate_templated_packer_for_type(tp, proxy)
                    STMT("internal static readonly Packers.AbstractPacker _{0} = {1}", 
                        tp.stringify(), definition)
            
    def generate_templated_packers_impl(self, module, service, proxy):
        BLOCK = module.block
        STMT = module.stmt
        SEP = module.sep
        
        for tp in service.all_types:
            if isinstance(tp, (compiler.TList, compiler.TSet, compiler.TMap)) and is_complex_type(tp):
                definition = self._generate_templated_packer_for_type(tp, proxy)
                STMT("_{0} = {1}", tp.stringify(), definition)

    def generate_enum(self, module, enum):
        BLOCK = module.block
        STMT = module.stmt
        SEP = module.sep

        with BLOCK("public enum {0}", enum.name):
            for mem in enum.members[:-1]:
                STMT("{0} = {1}", mem.name, mem.value, suffix = ",")
            STMT("{0} = {1}", enum.members[-1].name, enum.members[-1].value, suffix = "")
        SEP()
        with BLOCK("internal class _{0}Packer : Packers.AbstractPacker", enum.name):
            with BLOCK("public override int getId()"):
                STMT("return {0}", enum.id)
            with BLOCK("public override void pack(object obj, Stream stream)"):
                STMT("Packers.Int32.pack((int)(({0})obj), stream)", enum.name)
            with BLOCK("public override object unpack(Stream stream)"):
                STMT("return ({0})((int)Packers.Int32.unpack(stream))", enum.name)
        SEP()
        STMT("internal static _{0}Packer {0}Packer = new _{0}Packer()", enum.name)

    def generate_record_class(self, module, rec, proxy):
        BLOCK = module.block
        STMT = module.stmt
        SEP = module.sep

        is_exc = isinstance(rec, compiler.Exception)

        with BLOCK("public class {0}{1}", rec.name, " : PackedException" if is_exc else ""):
            for mem in rec.members:
                STMT("public {0} {1}", type_to_cs(mem.type, proxy = proxy), mem.name)
            SEP()
            with BLOCK("public {0}()", rec.name):
                pass
            if rec.members:
                args = ", ".join("%s %s" % (type_to_cs(mem.type, proxy = proxy), mem.name) 
                    for mem in rec.members)
                with BLOCK("public {0}({1})", rec.name, args):
                    for mem in rec.members:
                        STMT("this.{0} = {0}", mem.name)
            SEP()
            with BLOCK("public override string ToString()"):
                if not rec.members:
                    STMT('return "{0}()"', rec.name)
                else:
                    STMT('return "{0}(" + {1} + ")"', rec.name, ' + ", " + '.join(mem.name
                        for mem in rec.members))

    def generate_record_packer(self, module, rec, static, proxy):
        BLOCK = module.block
        STMT = module.stmt
        SEP = module.sep

        with BLOCK("internal sealed class _{0}Packer : Packers.AbstractPacker", rec.name):
            if not static:
                complex_types = rec.get_complex_types()
                for tp in complex_types:
                    STMT("internal Packers.AbstractPacker {0}", type_to_packer(tp))
                args =  ", ".join("Packers.AbstractPacker %s" % (type_to_packer(tp),) 
                    for tp in complex_types)
                with BLOCK("public _{0}Packer({1})", rec.name, args):
                    for tp in complex_types:
                        STMT("this.{0} = {0}", type_to_packer(tp))
                SEP()

            with BLOCK("public override int getId()"):
                STMT("return {0}", rec.id)

            with BLOCK("public override void pack(object obj, Stream stream)"):
                STMT("{0} val = ({0})obj", rec.name)
                for mem in rec.members:
                    STMT("{0}.pack(val.{1}, stream)", type_to_packer(mem.type), mem.name)

            with BLOCK("public override object unpack(Stream stream)"):
                with BLOCK("return new {0}(", rec.name, prefix = "", suffix = ");"):
                    for mem in rec.members[:-1]:
                        STMT("({0}){1}.unpack(stream)", type_to_cs(mem.type, proxy = proxy), 
                            type_to_packer(mem.type), suffix = ",")
                    if rec.members:
                        mem = rec.members[-1]
                        STMT("({0}){1}.unpack(stream)", type_to_cs(mem.type, proxy = proxy), 
                            type_to_packer(mem.type), suffix = "")
        SEP()
        if static:
            STMT("internal static readonly _{0}Packer {0}Packer = new _{0}Packer()", rec.name)
        else:
            STMT("internal readonly _{0}Packer {0}Packer", rec.name)

    def generate_base_class_proxy(self, module, service):
        BLOCK = module.block
        STMT = module.stmt
        SEP = module.sep

        with BLOCK("public abstract class BaseProxy : IDisposable"):
            STMT("internal readonly long _objref")
            STMT("protected readonly Client _client")
            STMT("protected bool _disposed")
            SEP()
            with BLOCK("protected BaseProxy(Client client, long objref, bool owns_ref)"):
                STMT("_client = client")
                STMT("_objref = objref")
                STMT("_disposed = owns_ref ? false : true")
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
                    STMT("_client._utils.Decref(_objref)")
            SEP()
            with BLOCK("public override string ToString()"):
                STMT('return base.ToString() + "<" + _objref + ">"')

    def generate_class_interface(self, module, cls):
        BLOCK = module.block
        STMT = module.stmt
        SEP = module.sep
        DOC = module.doc

        if cls.extends:
            extends = " : " + ", ".join("I%s" % (c.name,) for c in cls.extends)
        else:
            extends = ""

        with BLOCK("public interface I{0}{1}", cls.name, extends):
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
                args = ", ".join("%s %s" % (type_to_cs(arg.type), arg.name) 
                    for arg in method.args)
                STMT("{0} {1}({2})", type_to_cs(method.type), method.name, args)

    def generate_class_proxy(self, module, service, cls):
        BLOCK = module.block
        STMT = module.stmt
        SEP = module.sep
        DOC = module.doc

        with BLOCK("public class {0}Proxy : BaseProxy", cls.name):
            with BLOCK("internal {0}Proxy(Client client, long objref, bool owns_ref) :"
                    " base(client, objref, owns_ref)", cls.name):
                pass
            SEP()
            for attr in cls.all_attrs:
                with BLOCK("public {0} {1}", type_to_cs(attr.type, proxy = True), attr.name):
                    if attr.get:
                        with BLOCK("get"):
                            STMT("return _client._funcs.sync_{0}(this)", attr.getter.id)
                    if attr.set:
                        with BLOCK("set"):
                            STMT("_client._funcs.sync_{0}(this, value)", attr.setter.id)
            SEP()
            for method in cls.all_methods:
                if not method.clientside:
                    continue
                args = ", ".join("%s %s" % (type_to_cs(arg.type, proxy = True), arg.name) 
                    for arg in method.args)
                with BLOCK("public {0} {1}({2})", type_to_cs(method.type, proxy = True), method.name, args):
                    callargs = ["this"] + [arg.name for arg in method.args]
                    if method.type == compiler.t_void:
                        STMT("_client._funcs.sync_{0}({1})", method.func.id, ", ".join(callargs))
                    else:
                        STMT("return _client._funcs.sync_{0}({1})", method.func.id, ", ".join(callargs))
            if cls.all_derived:
                SEP()
                DOC("downcasts")
                for cls2 in cls.all_derived:
                    with BLOCK("public {0} CastTo{1}()", type_to_cs(cls2, proxy = True), cls2.name):
                        STMT("return new {0}(_client, _objref, false)", type_to_cs(cls2, proxy = True))
            if cls.all_bases:
                SEP()
                DOC("upcasts")
                for cls2 in cls.all_bases:
                    with BLOCK("public {0} CastTo{1}()", type_to_cs(cls2, proxy = True), cls2.name):
                        STMT("return new {0}(_client, _objref, false)", type_to_cs(cls2, proxy = True))

    def generate_handler_interface(self, module, service):
        BLOCK = module.block
        STMT = module.stmt
        SEP = module.sep

        with BLOCK("public interface IHandler"):
            for member in service.funcs.values():
                if isinstance(member, compiler.Func):
                    args = ", ".join("%s %s" % (type_to_cs(arg.type), arg.name) 
                        for arg in member.args)
                    STMT("{0} {1}({2})", type_to_cs(member.type), member.fullname, args)

    def generate_processor(self, module, service):
        BLOCK = module.block
        STMT = module.stmt
        SEP = module.sep

        with BLOCK("public partial class Processor : Protocol.BaseProcessor"):
            STMT("internal readonly IHandler handler")
            SEP()
            for cls in service.classes():
                STMT("internal readonly Packers.ObjRef {0}ObjRef", cls.name)
            SEP()
            generated_records = []
            for rec in service.records(is_complex_type):
                self.generate_record_packer(module, rec, static = False, proxy = False)
                generated_records.append(rec)
                SEP()
            self.generate_templated_packers_decl(module, service, proxy = False)
            SEP()
            STMT("protected readonly Packers.HeteroMapPacker heteroMapPacker")
            SEP()
            with BLOCK("public Processor(ITransport transport, IHandler handler) : base(transport)"):
                STMT("this.handler = handler")
                for cls in service.classes():
                    STMT("{0}ObjRef = new Packers.ObjRef({1}, this)", cls.name, cls.id)
                for rec in generated_records:
                    complex_types = rec.get_complex_types()
                    STMT("{0}Packer = new _{0}Packer({1})", rec.name, ", ".join(type_to_packer(tp) 
                        for tp in complex_types))
                self.generate_templated_packers_impl(module, service, proxy = False)
                SEP()
                STMT("Dictionary<int, Packers.AbstractPacker> packersMap = new Dictionary<int, Packers.AbstractPacker>()")
                for tp in service.ordered_types:
                    STMT("packersMap[{0}] = {1}", tp.id, type_to_packer(tp))
                STMT("heteroMapPacker = new Packers.HeteroMapPacker(999, packersMap)")
                STMT("packersMap[999] = heteroMapPacker")
            SEP()
            self.generate_process_getinfo(module, service)
            SEP()
            self.generate_process_invoke(module, service)
            SEP()

    def generate_processor_factory(self, module, service):
        BLOCK = module.block
        STMT = module.stmt
        SEP = module.sep
        
        with BLOCK("public class ProcessorFactory : Protocol.IProcessorFactory"):
            STMT("internal readonly IHandler handler")
            with BLOCK("public ProcessorFactory(IHandler handler)"):
                STMT("this.handler = handler")
            with BLOCK("public Protocol.BaseProcessor Create(ITransport transport)"):
                STMT("return new Processor(transport, this.handler)")
        SEP()

    def generate_process_getinfo(self, module, service):
        BLOCK = module.block
        STMT = module.stmt
        SEP = module.sep

        has_annotations = False
        for func in service.funcs.values(): 
            if func.annotations:
                has_annotations = True
                break
        
        with BLOCK("protected override void processGetServiceInfo(HeteroMap map)"):
            STMT('map["AGNOS_PROTOCOL_VERSION"] = AGNOS_PROTOCOL_VERSION')
            STMT('map["AGNOS_TOOLCHAIN_VERSION"] = AGNOS_TOOLCHAIN_VERSION')
            STMT('map["IDL_MAGIC"] = IDL_MAGIC')
            STMT('map["SERVICE_NAME"] = "{0}"', service.name)
            STMT('map.Add("SUPPORTED_VERSIONS", SUPPORTED_VERSIONS, Packers.listOfStr)')
        SEP()
        ##
        with BLOCK("protected override void processGetFunctionsInfo(HeteroMap map)"):
            STMT("HeteroMap funcinfo")
            STMT("Dictionary<string, string> args")
            if has_annotations:
                STMT("Dictionary<string, string> anno")
            SEP()
            for func in service.funcs.values():
                STMT("funcinfo = new HeteroMap()")
                STMT('funcinfo["name"] = "{0}"', func.name)
                STMT('funcinfo["type"] = "{0}"', str(func.type))
                STMT("args = new Dictionary<string, string>()")
                for arg in func.args:
                    STMT('args["{0}"] = "{1}"', arg.name, str(arg.type))
                STMT('funcinfo.Add("args", args, Packers.mapOfStrStr)')
                if func.annotations:
                    STMT("anno = new Dictionary<string, string>()")
                    for anno in func.annotations:
                        STMT('anno["{0}"] = "{1}"', anno.name, anno.value)
                    STMT('funcinfo.Add("annotations", anno, Packers.mapOfStrStr)')
                STMT('map.Add({0}, funcinfo, Packers.builtinHeteroMapPacker)', func.id)
        SEP()
        ##
        with BLOCK("protected override void processGetReflectionInfo(HeteroMap map)"):
            STMT("List<String> arg_names, arg_types")
            STMT("HeteroMap group, members, member");
            if has_annotations:
                STMT("Dictionary<string, string> anno")
            SEP()

            STMT('group = map.AddNewMap("enums")')
            for enum in service.enums():
                STMT('members = group.AddNewMap("{0}")', enum.name)
                for mem in enum.members:
                    STMT('members["{0}"] = "{1}"', mem.name, mem.value)
            SEP()
            STMT('group = map.AddNewMap("records")')
            for rec in service.records():
                STMT('members = group.AddNewMap("{0}")', rec.name)
                for mem in rec.members:
                    STMT('members["{0}"] = "{1}"', mem.name, mem.type)
            SEP()
            
            STMT('group = map.AddNewMap("classes")')
            if service.classes():
                STMT("HeteroMap cls_group, attr_group, meth_group, a, m")
            has_extends = False
            
            for cls in service.classes():
                STMT('cls_group = group.AddNewMap("{0}")', cls.name)
                if cls.extends:
                    if not has_extends:
                        has_extends = True
                        STMT('List<String> extendsList')
                    STMT('extendsList = new List<String>()')
                    for cls2 in cls.extends:
                        STMT('extendsList.Add("{0}")', cls2.name)
                    STMT('cls_group.Add("extends", Packers.Str, extendsList, Packers.listOfStr)')
                
                STMT('attr_group = cls_group.AddNewMap("attrs")')
                STMT('meth_group = cls_group.AddNewMap("methods")')
                for attr in cls.attrs:
                    STMT('a = attr_group.AddNewMap("{0}")', attr.name)
                    STMT('a["type"] = "{0}"', str(attr.type))
                    STMT('a["get"] = {0}', "true" if attr.get else "false")
                    STMT('a["set"] = {0}', "true" if attr.set else "false")
                    STMT('a["get-id"] = {0}', attr.getid)
                    STMT('a["set-id"] = {0}', attr.setid)
                    if attr.annotations:
                        STMT("anno = new Dictionary<string, string>()")
                        for anno in attr.annotations:
                            STMT('anno["{0}"] = "{1}"', anno.name, anno.value)
                        STMT('a.Add("annotations", anno, Packers.mapOfStrStr)')

                for meth in cls.methods:
                    STMT('m = meth_group.AddNewMap("{0}")', meth.name)
                    STMT('m["type"] = "{0}"', meth.type)
                    STMT('m["id"] = {0}', meth.id)
                    STMT("arg_names = new List<String>()")
                    STMT("arg_types = new List<String>()")
                    for arg in meth.args:
                        STMT('arg_names.Add("{0}")', arg.name)
                        STMT('arg_types.Add("{0}")', str(arg.type))
                    STMT('m.Add("arg_names", Packers.Str, arg_names, Packers.listOfStr)')
                    STMT('m.Add("arg_types", Packers.Str, arg_types, Packers.listOfStr)')
                    if meth.annotations:
                        STMT("anno = new Dictionary<string, string>()")
                        for anno in meth.annotations:
                            STMT('anno["{0}"] = "{1}"', anno.name, anno.value)
                        STMT('m.Add("annotations", anno, Packers.mapOfStrStr)')

            SEP()
            
            STMT('group = map.AddNewMap("functions")')
            for func in service.funcs.values():
                if not isinstance(func, compiler.Func):
                    continue
                STMT('member = group.AddNewMap("{0}")', func.dotted_fullname)
                STMT('member["id"] = {0}', str(func.id))
                STMT('member["type"] = "{0}"', str(func.type))
                if func.annotations:
                    STMT("anno = new Dictionary<string, string>()")
                    for anno in func.annotations:
                        STMT('anno["{0}"] = "{1}"', anno.name, anno.value)
                    STMT('member.Add("annotations", Packers.Str, anno, Packers.mapOfStrStr)')
                STMT("arg_names = new List<String>()")
                STMT("arg_types = new List<String>()")
                for arg in func.args:
                    STMT('arg_names.Add("{0}")', arg.name)
                    STMT('arg_types.Add("{0}")', str(arg.type))
                STMT('member.Add("arg_names", Packers.Str, arg_names, Packers.listOfStr)')
                STMT('member.Add("arg_types", Packers.Str, arg_types, Packers.listOfStr)')
            SEP()
            
            STMT('group = map.AddNewMap("consts")')
            for const in service.consts.values():
                STMT('member = group.AddNewMap("{0}")', const.dotted_fullname)
                STMT('member["type"] = "{0}"', str(const.type))
                STMT('member["value"] = "{0}"', const.value)
        SEP()
    
    def generate_process_invoke(self, module, service):
        BLOCK = module.block
        STMT = module.stmt
        SEP = module.sep

        with BLOCK("override protected void processInvoke(int seq)"):
            STMT("Packers.AbstractPacker packer = null")
            STMT("object result = null")
            STMT("object inst = null")
            STMT("object[] args = null")
            STMT("Stream stream = transport.GetStream()")
            STMT("int funcid = (int){0}.unpack(stream)", type_to_packer(compiler.t_int32))
            packed_exceptions = service.exceptions()

            with BLOCK("try") if packed_exceptions else NOOP:
                with BLOCK("switch (funcid)"):
                    for func in service.funcs.values():
                        with BLOCK("case {0}:", func.id, prefix = None, suffix = None):
                            self.generate_invocation_case(module, func)
                            if func.type != compiler.t_void:
                                STMT("packer = {0}", type_to_packer(func.type))
                            STMT("break")
                    with BLOCK("default:", prefix = None, suffix = None):
                        STMT('throw new ProtocolError("unknown function id: " + funcid)')
                SEP()
                STMT("{0}.pack((byte)Protocol.REPLY_SUCCESS, stream)", type_to_packer(compiler.t_int8))
                with BLOCK("if (packer != null)"):
                    STMT("packer.pack(result, stream)")
            for tp in packed_exceptions:
                with BLOCK("catch ({0} ex)", tp.name):
                    STMT("transport.Reset()")
                    STMT("{0}.pack((byte)Protocol.REPLY_PACKED_EXCEPTION, stream)", 
                        type_to_packer(compiler.t_int8))
                    STMT("{0}.pack({1}, stream)", type_to_packer(compiler.t_int32), tp.id)
                    STMT("{0}.pack(ex, stream)", type_to_packer(tp))

    def generate_invocation_case(self, module, func):
        BLOCK = module.block
        STMT = module.stmt
        SEP = module.sep
        
        if isinstance(func, compiler.Func):
            if func.args:
                with BLOCK("args = new object[] {0}", "{", prefix = "", suffix = "};"):
                    for arg in func.args[:-1]:
                        STMT("{0}.unpack(stream)", type_to_packer(arg.type), suffix = ",")
                    if func.args:
                        arg = func.args[-1]
                        STMT("{0}.unpack(stream)", type_to_packer(arg.type), suffix = ",")
            callargs = ", ".join("(%s)args[%s]" % (type_to_cs(arg.type), i) 
                for i, arg in enumerate(func.args))
            if func.type == compiler.t_void:
                invocation = "handler.%s(%s)" % (func.fullname, callargs) 
            else:
                invocation = "result = handler.%s(%s)" % (func.fullname, callargs)
        else:
            insttype = func.args[0].type
            STMT("inst = ({0})({1}.unpack(stream))", 
                type_to_cs(insttype), type_to_packer(insttype))

            if len(func.args) > 1:
                with BLOCK("args = new object[] {0}", "{", prefix = "", suffix = "};"):
                    for arg in func.args[1:-1]:
                        STMT("{0}.unpack(stream)", type_to_packer(arg.type), suffix = ",")
                    arg = func.args[-1]
                    STMT("{0}.unpack(stream)", type_to_packer(arg.type), suffix = ",")
            callargs = ", ".join("(%s)args[%s]" % (type_to_cs(arg.type), i) 
                for i, arg in enumerate(func.args[1:]))
            
            if isinstance(func.origin, compiler.ClassAttr):
                if func.type == compiler.t_void:
                    invocation = "((%s)inst).%s = (%s)args[0]" % (type_to_cs(insttype), 
                        func.origin.name, type_to_cs(func.origin.type))
                else:
                    invocation = "result = ((%s)inst).%s" % (type_to_cs(insttype), func.origin.name)
            else:
                if func.type == compiler.t_void:
                    invocation = "((%s)inst).%s(%s)" % (type_to_cs(insttype), func.origin.name, callargs)
                else:
                    invocation = "result = ((%s)inst).%s(%s)" % (type_to_cs(insttype), func.origin.name, callargs)
        
        with BLOCK("try {0}", "{", prefix = ""):
            STMT(invocation)
        with BLOCK("catch (PackedException ex) {0}", "{", prefix = ""):
            STMT("throw ex")
        with BLOCK("catch (Exception ex) {0}", "{", prefix = ""):
            STMT("throw new GenericException(ex.Message, ex.StackTrace)")

    #===========================================================================
    # client
    #===========================================================================

    def generate_client(self, module, service):
        BLOCK = module.block
        STMT = module.stmt
        SEP = module.sep
        DOC = module.doc
        
        with BLOCK("public partial class Client : Protocol.BaseClient"):
            for cls in service.classes():
                STMT("internal readonly Packers.ObjRef {0}ObjRef", cls.name)
            SEP()
            generated_records = []
            for rec in service.records(is_complex_type):
                self.generate_record_packer(module, rec, static = False, proxy = True)
                generated_records.append(rec)
                SEP()
            self.generate_templated_packers_decl(module, service, proxy = True)
            SEP()
            with BLOCK("internal abstract class ClientSerializer : Packers.ISerializer"):
                STMT("public Client client")
                SEP()
                with BLOCK("public ClientSerializer(Client client)"):
                    STMT("this.client = client")
                SEP()
                with BLOCK("public long store(object obj)"):
                    with BLOCK("if (obj == null)"):
                        STMT("return -1")
                    STMT("return ((BaseProxy)obj)._objref")
                SEP()
                with BLOCK("public object load(long id)"):
                    with BLOCK("if (id < 0)"):
                        STMT("return null")
                    STMT("object proxy = client._utils.GetProxy(id)")
                    with BLOCK("if (proxy == null)"):
                        STMT("proxy = newProxy(id)")
                        STMT("client._utils.CacheProxy(id, proxy)")
                    STMT("return proxy")
                STMT("protected abstract object newProxy(long id)")
            SEP()
            for cls in service.classes():
                with BLOCK("internal class {0}ClientSerializer : ClientSerializer", cls.name):
                    with BLOCK("public {0}ClientSerializer(Client client) : base(client)", cls.name):
                        pass
                    with BLOCK("protected override object newProxy(long id)"):
                        STMT("return new {0}(client, id, true)", type_to_cs(cls, proxy = True))
            SEP()
            STMT("protected readonly Packers.HeteroMapPacker heteroMapPacker")
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

    def generate_client_ctor(self, module, service, namespaces, generated_records):
        BLOCK = module.block
        STMT = module.stmt
        SEP = module.sep
        DOC = module.doc
        
        with BLOCK("public Client(ITransport transport)"):
            STMT("Dictionary<int, Packers.AbstractPacker> pem = new Dictionary<int, Packers.AbstractPacker>()") 
            STMT("_utils = new Protocol.ClientUtils(transport, pem)")
            STMT("_funcs = new _Functions(this)")
            SEP()
            for cls in service.classes():
                STMT("{0}ObjRef = new Packers.ObjRef({1}, new {0}ClientSerializer(this))", cls.name, cls.id) 
            
            for rec in generated_records:
                complex_types = rec.get_complex_types()
                STMT("{0}Packer = new _{0}Packer({1})", rec.name, ", ".join(type_to_packer(tp) 
                    for tp in complex_types))
            SEP()
            
            for exc in service.exceptions():
                STMT("pem[{0}] = {1}Packer", exc.id, exc.name)
            SEP()
            
            for name, id in namespaces:
                STMT("{0} = new _Namespace{1}(_funcs)", name, id)
            
            self.generate_templated_packers_impl(module, service, proxy = True)
            SEP()
            
            STMT("Dictionary<int, Packers.AbstractPacker> packersMap = new Dictionary<int, Packers.AbstractPacker>()")
            for tp in service.ordered_types:
                STMT("packersMap[{0}] = {1}", tp.id, type_to_packer(tp))
            STMT("heteroMapPacker = new Packers.HeteroMapPacker(999, packersMap)")
            STMT("packersMap[999] = heteroMapPacker")

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
        with BLOCK("public sealed class _Namespace{0}", root["__id__"]):
            subnamespaces = []
            STMT("internal readonly _Functions _funcs")
            SEP()
            for name, node in root.iteritems():
                if isinstance(node, dict):
                    self.generate_client_namespace_classes(module, node)
                    subnamespaces.append((name, node["__id__"]))
                elif isinstance(node, compiler.Func):
                    func = node
                    args = ", ".join("%s %s" % (type_to_cs(arg.type, proxy = True), arg.name) 
                        for arg in func.args)
                    callargs = ", ".join(arg.name for arg in func.args)
                    with BLOCK("public {0} {1}({2})", type_to_cs(func.type, proxy = True), func.name, args):
                        if func.type == compiler.t_void:
                            STMT("_funcs.sync_{0}({1})", func.id, callargs)
                        else:
                            STMT("return _funcs.sync_{0}({1})", func.id, callargs)
                elif isinstance(node, compiler.Const):
                    STMT("public const {0} {1} = {2}", type_to_cs(node.type), 
                        node.name, const_to_cs(node.type, node.value))
                else:
                    pass
            SEP()
            with BLOCK("internal _Namespace{0}(_Functions funcs)", root["__id__"]):
                STMT("_funcs = funcs")
                for name, id in subnamespaces:
                    STMT("{0} = new _Namespace{1}(funcs)", name, id)
        STMT("public readonly _Namespace{0} {1}", root["__id__"], root["__name__"])

    def generate_client_helpers(self, module, service):
        BLOCK = module.block
        STMT = module.stmt
        SEP = module.sep
        
        with BLOCK("public static Client ConnectSock(string host, int port)"):
            STMT("return new Client(new SocketTransport(host, port))")
        with BLOCK("public static Client ConnectSock(Socket sock)"):
            STMT("return new Client(new SocketTransport(sock))")
        
        with BLOCK("public static Client ConnectProc(string executable)"):
            STMT("return new Client(ProcTransport.Connect(executable))")
        with BLOCK("public static Client ConnectProc(Process proc)"):
            STMT("return new Client(ProcTransport.Connect(proc))")

        with BLOCK("public static Client ConnectUri(string uri)"):
            STMT("return new Client(new HttpClientTransport(uri))")
        with BLOCK("public static Client ConnectUri(Uri uri)"):
            STMT("return new Client(new HttpClientTransport(uri))")

        SEP()
        with BLOCK("public void AssertServiceCompatibility()"):
            STMT("HeteroMap info = GetServiceInfo(Protocol.INFO_SERVICE)")
            STMT('string agnos_protocol_version = (string)info["AGNOS_PROTOCOL_VERSION"]')
            STMT('string service_name = (string)info["SERVICE_NAME"]')
            
            with BLOCK('if (agnos_protocol_version != AGNOS_PROTOCOL_VERSION)'):
                STMT('''throw new WrongAgnosVersion("expected protocol '" + AGNOS_PROTOCOL_VERSION + "', found '" + agnos_protocol_version + "'")''')
            with BLOCK('if (service_name != "{0}")', service.name):
                STMT('''throw new WrongServiceName("expected service '{0}', found '" + service_name + "'")''', service.name)
            if service.clientversion:
                STMT("object output = null")
                STMT('info.TryGetValue("SUPPORTED_VERSIONS", out output)')
                STMT('List<string> supported_versions = (List<string>)output')
                with BLOCK('if (supported_versions == null || !supported_versions.Contains(CLIENT_VERSION))'):
                    STMT('''throw new IncompatibleServiceVersion("server does not support client version '" + CLIENT_VERSION + "'")''')
    
    def generate_client_internal_funcs(self, module, service):
        BLOCK = module.block
        STMT = module.stmt
        SEP = module.sep
        DOC = module.doc
        with BLOCK("internal sealed class _Functions"):
            STMT("internal readonly Client client")
            with BLOCK("public _Functions(Client client)"):
                STMT("this.client = client")
            SEP()
            for func in service.funcs.values():
                args = ", ".join("%s %s" % (type_to_cs(arg.type, proxy = True), arg.name) 
                    for arg in func.args)
                with BLOCK("public {0} sync_{1}({2})", type_to_cs(func.type, proxy = True), 
                        func.id, args):
                    if is_complex_type(func.type):
                        STMT("int seq = client._utils.BeginCall({0}, client.{1})", 
                            func.id, type_to_packer(func.type))
                    else:
                        STMT("int seq = client._utils.BeginCall({0}, {1})", func.id, 
                            type_to_packer(func.type))
                    if func.args:
                        STMT("Stream stream = client._utils.transport.GetStream()")
                        with BLOCK("try"):
                            for arg in func.args:
                                if is_complex_type(arg.type):
                                    STMT("client.{0}.pack({1}, stream)", type_to_packer(arg.type), arg.name)
                                else:
                                    STMT("{0}.pack({1}, stream)", type_to_packer(arg.type), arg.name)
                        with BLOCK("catch (Exception ex)"):
                            STMT("client._utils.CancelCall()")
                            STMT("throw ex")
                    STMT("client._utils.EndCall()")
                    if func.type == compiler.t_void:
                        STMT("client._utils.GetReply(seq)")
                    else:
                        STMT("return ({0})client._utils.GetReply(seq)", type_to_cs(func.type, proxy = True))
                SEP()
        SEP()
        STMT("internal readonly _Functions _funcs")
    
    def generate_client_funcs(self, module, service):
        BLOCK = module.block
        STMT = module.stmt
        SEP = module.sep
        DOC = module.doc
        for func in service.funcs.values():
            if not isinstance(func, compiler.Func) or func.namespace or not func.clientside:
                continue
            args = ", ".join("%s %s" % (type_to_cs(arg.type, proxy = True), arg.name) 
                for arg in func.args)
            callargs = ", ".join(arg.name for arg in func.args)
            with BLOCK("public {0} {1}({2})", type_to_cs(func.type, proxy = True), func.name, args):
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

        STMT("using System")
        STMT("using System.Collections.Generic")
        STMT("using {0}.ServerBindings", service.package2)
        SEP()
        with BLOCK("public class ServerStub"):
            DOC("classes", spacer = True)
            for cls in service.classes():
                with BLOCK("public class {0} : {1}", cls.name, type_to_cs_full(cls, service)):
                    for attr in cls.all_attrs:
                        STMT("protected {0} _{1}", type_to_cs_full(attr.type, service), attr.name)
                    SEP()
                    args = ", ".join("%s %s" % (type_to_cs_full(attr.type, service), attr.name) for attr in cls.all_attrs)
                    with BLOCK("public {0}({1})", cls.name, args):
                        for attr in cls.all_attrs:
                            STMT("_{0} = {0}", attr.name)
                    SEP()
                    for attr in cls.all_attrs:
                        with BLOCK("public {0} {1}", type_to_cs_full(attr.type, service), attr.name):
                            if attr.get:
                                with BLOCK("get"):
                                    STMT("return _{0}", attr.name)
                            if attr.set:
                                with BLOCK("set"):
                                    STMT("_{0} = value", attr.name)
                        SEP()
                    for method in cls.all_methods:
                        args = ", ".join("%s %s" % (type_to_cs_full(arg.type, service), arg.name) 
                            for arg in method.args)
                        with BLOCK("public {0} {1}({2})", type_to_cs_full(method.type, service), method.name, args):
                            DOC("implement me")
                        SEP()
                SEP()
            DOC("handler", spacer = True)
            with BLOCK("public class Handler : {0}.IHandler", service.name):
                for member in service.funcs.values():
                    if not isinstance(member, compiler.Func):
                        continue
                    args = ", ".join("%s %s" % (type_to_cs_full(arg.type, service), arg.name) 
                        for arg in member.args)
                    with BLOCK("public {0} {1}({2})", 
                            type_to_cs_full(member.type, service), member.fullname, args):
                        DOC("implement me")
                    SEP()
            SEP()
            DOC("main", spacer = True)
            with BLOCK("public static void Main(string[] args)"):
                STMT("Agnos.Servers.CmdlineServer server = new Agnos.Servers.CmdlineServer("
                    "new {0}.ProcessorFactory(new Handler()))", service.name)
                STMT("server.Main(args)")
            SEP()





