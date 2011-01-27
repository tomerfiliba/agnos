##############################################################################
# Part of the Agnos RPC Framework
#    http://agnos.sourceforge.net
#
# Copyright 2011, International Business Machines Corp.
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
from .base import TargetBase
from .. import compiler
from ..compiler import is_complex_type


def type_to_packer(t):
    if t == compiler.t_void:
        return "None"
    elif t == compiler.t_bool:
        return "packers.Bool"
    elif t == compiler.t_int8:
        return "packers.Int8"
    elif t == compiler.t_int16:
        return "packers.Int16"
    elif t == compiler.t_int32:
        return "packers.Int32"
    elif t == compiler.t_int64:
        return "packers.Int64"
    elif t == compiler.t_float:
        return "packers.Float"
    elif t == compiler.t_date:
        return "packers.Date"
    elif t == compiler.t_buffer:
        return "packers.Buffer"
    elif t == compiler.t_string:
        return "packers.Str"
    elif t == compiler.t_heteromap:
        return "heteroMapPacker"
    elif isinstance(t, (compiler.TList, compiler.TSet, compiler.TMap)):
        return "_%s" % (t.stringify(),)
    elif isinstance(t, (compiler.Enum, compiler.Record, compiler.ExceptionRecord)):
        return "%sPacker" % (t.name,)
    elif isinstance(t, compiler.Class):
        return "%sObjRef" % (t.name,)
    elif isinstance(t, compiler.Typedef):
        return type_to_packer(t.type)
    else:
        assert False

def const_to_python(typ, val):
    if val is None:
        return "None"
    elif typ == compiler.t_bool:
        if val:
            return "True"
        else:
            return "False"
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
    elif isinstance(typ, compiler.TList):
        return "[%s]" % (", ".join(const_to_python(typ.oftype, item) for item in val),)
    else:
        raise IDLError("%r cannot be converted to a python const" % (val,))


class PythonTarget(TargetBase):
    from ..langs import python
    LANGUAGE = python

    def generate(self, service):
        with self.new_module("%s_bindings.py" % (service.name,)) as module:
            BLOCK = module.block
            STMT = module.stmt
            SEP = module.sep
            DOC = module.doc
            
            STMT("import agnos")
            STMT("from agnos import packers")
            STMT("from agnos import utils")
            STMT("from functools import partial")
            SEP()
            
            STMT("AGNOS_TOOLCHAIN_VERSION = '{0}'", compiler.AGNOS_TOOLCHAIN_VERSION)
            STMT("AGNOS_PROTOCOL_VERSION = '{0}'", compiler.AGNOS_PROTOCOL_VERSION)
            STMT("IDL_MAGIC = '{0}'", service.digest)
            if not service.clientversion:
                STMT("CLIENT_VERSION = None")
            else:
                STMT("CLIENT_VERSION = '{0}'", service.clientversion)
            STMT("SUPPORTED_VERSIONS = {0}", service.versions)
            SEP()
            
            DOC("enums", spacer = True)
            for enum in service.enums():
                self.generate_enum(module, enum)
                SEP()
            
            DOC("records", spacer = True)
            for rec in service.records():
                self.generate_record_class(module, rec)
                SEP()

            for rec in service.exceptions():
                self.generate_exception_record(module, rec)
                SEP()

            for rec in service.records_and_exceptions(lambda mem: not is_complex_type(mem)):
                self.generate_record_packer(module, rec)
                SEP()
            
            DOC("consts", spacer = True)
            for member in service.consts.values():
                STMT("{0} = {1}", member.fullname, 
                    const_to_python(member.type, member.value))
            SEP()
            
            DOC("classes", spacer = True)
            for cls in service.classes():
                self.generate_class_proxy(module, service, cls)
                SEP()
            SEP()
            
            DOC("server", spacer = True)
            self.generate_handler_interface(module, service)
            SEP()
            
            self.generate_processor(module, service)
            SEP()
            
            DOC("client", spacer = True)
            self.generate_client(module, service)
            SEP()

    def _generate_templated_packer_for_type(self, tp):
        if isinstance(tp, compiler.TList):
            return "packers.ListOf(%s, %s)" % (tp.id, 
                self._generate_templated_packer_for_type(tp.oftype),)
        if isinstance(tp, compiler.TSet):
            return "packers.SetOf(%s, %s)" % (tp.id, 
                self._generate_templated_packer_for_type(tp.oftype),)
        elif isinstance(tp, compiler.TMap):
            return "packers.MapOf(%s, %s, %s)" % (tp.id, 
                self._generate_templated_packer_for_type(tp.keytype),
                self._generate_templated_packer_for_type(tp.valtype))
        else:
            return type_to_packer(tp)

    def generate_templated_packers(self, module, service):
        BLOCK = module.block
        STMT = module.stmt
        SEP = module.sep
        
        for tp in service.all_types:
            if isinstance(tp, (compiler.TList, compiler.TSet, compiler.TMap)):
                definition = self._generate_templated_packer_for_type(tp)
                STMT("_{0} = {1}", tp.stringify(), definition)

    def generate_enum(self, module, enum):
        BLOCK = module.block
        STMT = module.stmt
        SEP = module.sep
        
        members = ["\n    '%s' : %s" % (m.name, m.value) for m in enum.members]
        STMT("{0} = utils.create_enum('{0}', {{{1}}})", enum.name, ", ".join(members))
        SEP()
        with BLOCK("class {0}Packer(packers.Packer)", enum.name):
            STMT("@classmethod")
            with BLOCK("def get_id(cls)"):
                STMT("return {0}", enum.id)
            STMT("@classmethod")
            with BLOCK("def pack(cls, obj, stream)"):
                with BLOCK("if isinstance(obj, utils.Enum)"):
                    STMT("packers.Int32.pack(obj.value, stream)")
                with BLOCK("else"):
                    STMT("packers.Int32.pack(obj, stream)")
            STMT("@classmethod")
            with BLOCK("def unpack(cls, stream)"):
                STMT("return {0}.get_by_value(packers.Int32.unpack(stream))", enum.name)

    def generate_record_class(self, module, rec):
        BLOCK = module.block
        STMT = module.stmt
        SEP = module.sep
        
        with BLOCK("class {0}(agnos.BaseRecord)", rec.name):
            STMT('_idl_type = "{0}"', rec.name)
            STMT("_idl_id = {0}", rec.id)
            STMT("_idl_attrs = [{0}]", ", ".join(repr(mem.name) for mem in rec.members))
            SEP()
            args = ["%s = None" % (mem.name,) for mem in rec.members]
            with BLOCK("def __init__(self, {0})", ", ".join(args)):
                if not rec.members:
                    STMT("pass")
                for mem in rec.members:
                    STMT("self.{0} = {0}", mem.name)
            SEP()
            with BLOCK("def __repr__(self)"):
                attrs = ["self.%s" % (mem.name,) for mem in rec.members]
                STMT("attrs = [{0}]", ", ".join(attrs))
                STMT("return '{0}(%s)' % (', '.join(repr(a) for a in attrs),)", rec.name)

    def generate_exception_record(self, module, rec):
        BLOCK = module.block
        STMT = module.stmt
        SEP = module.sep
        
        with BLOCK("class {0}({1})", rec.name, rec.extends.name if rec.extends else "agnos.PackedException"):
            STMT('_idl_type = "{0}"', rec.name)
            STMT("_idl_id = {0}", rec.id)
            STMT("_idl_attrs = [{0}]", ", ".join(repr(mem.name) for mem in rec.members))
            SEP()
            args = ["%s = None" % (mem.name,) for mem in rec.members]
            with BLOCK("def __init__(self, {0})", ", ".join(args)):
                if not rec.members:
                    STMT("pass")
                for mem in rec.members:
                    STMT("self.{0} = {0}", mem.name)
            SEP()
            with BLOCK("def __repr__(self)"):
                attrs = ["self.%s" % (mem.name,) for mem in rec.members]
                STMT("attrs = [{0}]", ", ".join(attrs))
                STMT("return '{0}(%s)' % (', '.join(repr(a) for a in attrs),)", rec.name)

    def generate_record_packer(self, module, rec):
        BLOCK = module.block
        STMT = module.stmt
        SEP = module.sep
        
        with BLOCK("class {0}Packer(packers.Packer)", rec.name):
            STMT("@classmethod")
            with BLOCK("def get_id(cls)"):
                STMT("return {0}", rec.id)

            STMT("@classmethod")
            with BLOCK("def pack(cls, obj, stream)"):
                if not rec.members:
                    STMT("pass")
                for mem in rec.members:
                    STMT("{0}.pack(obj.{1}, stream)", type_to_packer(mem.type), mem.name)

            STMT("@classmethod")
            with BLOCK("def unpack(cls, stream)"):
                with BLOCK("return {0}", rec.name, prefix = "(", suffix = ")"):
                    for mem in rec.members:
                        STMT("{0}.unpack(stream),", type_to_packer(mem.type))
    
    def generate_class_proxy(self, module, service, cls):
        BLOCK = module.block
        STMT = module.stmt
        SEP = module.sep
        DOC = module.doc
        with BLOCK("class {0}Proxy(agnos.BaseProxy)", cls.name):
            STMT('_idl_type = "{0}"', cls.name)
            STMT("__slots__ = []")
            SEP()
            for attr in cls.all_attrs:
                accessors = []
                if attr.get:
                    with BLOCK("def _get_{0}(self)", attr.name):
                        STMT("return self._client._funcs.sync_{0}(self)", attr.getter.id)
                    accessors.append("_get_%s" % (attr.name,))
                if attr.set:
                    with BLOCK("def _set_{0}(self, value)", attr.name):
                        STMT("self._client._funcs.sync_{0}(self, value)", attr.getter.id)
                    accessors.append("_set_%s" % (attr.name,))
                STMT("{0} = property({1})", attr.name, ", ".join(accessors))
            SEP()
            for method in cls.all_methods:
                if not method.clientside:
                    continue
                args = ", ".join(arg.name for arg in method.args)
                with BLOCK("def {0}(self, {1})", method.name, args):
                    callargs = ["self"] + [arg.name for arg in method.args]
                    STMT("return self._client._funcs.sync_{0}({1})", method.func.id, ", ".join(callargs))
            if cls.all_derived:
                SEP()
                DOC("downcasts")
                for cls2 in cls.all_derived:
                    with BLOCK("def cast_to_{0}()", cls2.name):
                        STMT("return {0}Proxy(self._client, self._objref, False)", cls2.name)
            if cls.all_bases:
                SEP()
                DOC("upcasts")
                for cls2 in cls.all_bases:
                    with BLOCK("def cast_to_{0}()", cls2.name):
                        STMT("return {0}Proxy(self._client, self._objref, False)", cls2.name)

    def generate_handler_interface(self, module, service):
        BLOCK = module.block
        STMT = module.stmt
        SEP = module.sep
        with BLOCK("class IHandler(object)"):
            STMT("__slots__ = []")
            for member in service.funcs.values():
                if isinstance(member, compiler.Func):
                    args = ", ".join(arg.name for arg in member.args)
                    with BLOCK("def {0}(self, {1})", member.fullname, args):
                        STMT("raise NotImplementedError()")

    def generate_processor(self, module, service):
        BLOCK = module.block
        STMT = module.stmt
        SEP = module.sep
        with BLOCK("class Processor(agnos.BaseProcessor)"):
            with BLOCK("def __init__(self, transport, handler, exception_map = {})"):
                STMT("agnos.BaseProcessor.__init__(self, transport)")
                for func in service.funcs.values():
                    self._generate_processor_function(module, func)
                    self._generate_processor_unpacker(module, func)
                SEP()
                STMT("self.exception_map = exception_map")
                STMT("storer = self.store")
                STMT("loader = self.load")
                for cls in service.classes():
                    STMT("{0}ObjRef = packers.ObjRef({1}, storer, loader)", cls.name, cls.id)
                SEP()
                STMT("packers_map = {}")
                STMT("heteroMapPacker = packers.HeteroMapPacker(999, packers_map)")
                STMT("packers_map[999] = heteroMapPacker")
                SEP()
                for rec in service.records_and_exceptions(is_complex_type):
                    self.generate_record_packer(module, rec)
                    SEP()
                self.generate_templated_packers(module, service)
                SEP()
                with BLOCK("self.func_mapping = ", prefix = "{", suffix = "}"):
                    for func in service.funcs.values():
                        STMT("{0} : (_func_{0}, _unpack_{0}, {1}),", 
                            func.id, type_to_packer(func.type))
                SEP()
                with BLOCK("self.packed_exceptions = ", prefix = "{", suffix = "}"):
                    for exc in service.exceptions():
                        STMT("{0} : {1},", exc.name, type_to_packer(exc))
                SEP()
                for tp in service.types.values():
                    STMT("packers_map[{0}] = {1}", tp.id, type_to_packer(tp))
            SEP()
            ######
            with BLOCK("def process_get_service_info(self, info)"):
                STMT('info["AGNOS_TOOLCHAIN_VERSION"] = AGNOS_TOOLCHAIN_VERSION')
                STMT('info["AGNOS_PROTOCOL_VERSION"] = AGNOS_PROTOCOL_VERSION')
                STMT('info["IDL_MAGIC"] = IDL_MAGIC')
                STMT('info["SERVICE_NAME"] = "{0}"', service.name)
                STMT('info.add("SUPPORTED_VERSIONS", packers.Str, SUPPORTED_VERSIONS, packers.list_of_str)')
            SEP()
            ######
            with BLOCK("def process_get_functions_info(self, info)"):
                for func in service.funcs.values():
                    STMT("funcinfo = info.new_map({0})", func.id)
                    STMT('funcinfo["name"] = "{0}"', func.name)
                    STMT('funcinfo["type"] = "{0}"', str(func.type))
                    STMT("arg_names = []")
                    STMT("arg_types = []")
                    for arg in func.args:
                        STMT('arg_names.append("{0}")', arg.name)
                        STMT('arg_types.append("{0}")', str(arg.type))
                    STMT('funcinfo.add("arg_names", packers.Str, arg_names, packers.list_of_str)')
                    STMT('funcinfo.add("arg_types", packers.Str, arg_types, packers.list_of_str)')
                    if func.annotations:
                        with BLOCK("anno = ", prefix = "{", suffix = "}"):
                            for anno in func.annotations:
                                STMT('"{0}" : "{1}",', anno.name, repr(anno.value))
                        STMT('funcinfo.add("annotations", packers. anno, packers.map_of_str_str)')
            SEP()
            ######
            with BLOCK("def process_get_reflection_info(self, info)"):
                STMT('group = info.new_map("enums")')
                for enum in service.enums():
                    STMT('members = group.new_map("{0}")', enum.name)
                    for mem in enum.members:
                        STMT('members["{0}"] = "{1}"', mem.name, mem.value)
                SEP()
                STMT('group = info.new_map("records")')
                for rec in service.records():
                    STMT('members = group.new_map("{0}")', rec.name)
                    for mem in rec.members:
                        STMT('members["{0}"] = "{1}"', mem.name, mem.type)
                SEP()
                STMT('group = info.new_map("exceptions")')
                for rec in service.exceptions():
                    STMT('members = group.new_map("{0}")', rec.name)
                    for mem in rec.local_members:
                        STMT('members["{0}"] = "{1}"', mem.name, mem.type)
                    STMT('members["__super__"] = "{0}"', rec.extends.name if rec.extends else "")
                SEP()
                STMT('group = info.new_map("classes")')
                for cls in service.classes():
                    STMT('cls_group = group.new_map("{0}")', cls.name)
                    if cls.extends:
                        STMT('cls_group.add("extends", packers.Str, {0}, packers.list_of_str)',
                            repr([cls2.name for cls2 in cls.extends]))
                    
                    STMT('attr_group = cls_group.new_map("attrs")')
                    STMT('meth_group = cls_group.new_map("methods")')
                    for attr in cls.attrs:
                        STMT('a = attr_group.new_map("{0}")', attr.name)
                        STMT('a["type"] = "{0}"', str(attr.type))
                        STMT('a["get"] = {0}', attr.get)
                        STMT('a["set"] = {0}', attr.set)
                        STMT('a["get-id"] = {0}', attr.getid)
                        STMT('a["set-id"] = {0}', attr.setid)
                        if attr.annotations:
                            with BLOCK("anno = ", prefix = "{", suffix = "}"):
                                for anno in attr.annotations:
                                    STMT('"{0}" : "{1}",', anno.name, repr(anno.value))
                            STMT('a.add("annotations", packers.Str, anno, packers.map_of_str_str)')
                    for meth in cls.methods:
                        STMT('m = meth_group.new_map("{0}")', meth.name)
                        STMT('m["type"] = "{0}"', meth.type)
                        STMT('m["id"] = {0}', meth.id)
                        if meth.annotations:
                            with BLOCK("anno = ", prefix = "{", suffix = "}"):
                                for anno in meth.annotations:
                                    STMT('"{0}" : "{1}",', anno.name, repr(anno.value))
                            STMT('m.add("annotations", packers.Str, anno, packers.map_of_str_str)')
                        STMT("arg_names = []")
                        STMT("arg_types = []")
                        for arg in meth.args:
                            STMT('arg_names.append("{0}")', arg.name)
                            STMT('arg_types.append("{0}")', str(arg.type))
                        STMT('m.add("arg_names", packers.Str, arg_names, packers.list_of_str)')
                        STMT('m.add("arg_types", packers.Str, arg_types, packers.list_of_str)')
                SEP()
                STMT('funcs = info.new_map("functions")')
                for func in service.funcs.values():
                    if not isinstance(func, compiler.Func):
                        continue
                    STMT('func = funcs.new_map("{0}")', func.dotted_fullname)
                    STMT('func["id"] = {0}', str(func.id))
                    STMT('func["type"] = "{0}"', str(func.type))
                    if func.annotations:
                        with BLOCK("anno = ", prefix = "{", suffix = "}"):
                            for anno in func.annotations:
                                STMT('"{0}" : "{1}",', anno.name, repr(anno.value))
                        STMT('func.add("annotations", packers.Str, anno, packers.map_of_str_str)')
                    STMT("arg_names = []")
                    STMT("arg_types = []")
                    for arg in func.args:
                        STMT('arg_names.append("{0}")', arg.name)
                        STMT('arg_types.append("{0}")', str(arg.type))
                    STMT('func.add("arg_names", packers.Str, arg_names, packers.list_of_str)')
                    STMT('func.add("arg_types", packers.Str, arg_types, packers.list_of_str)')
                SEP()
                STMT('consts = info.new_map("consts")')
                for const in service.consts.values():
                    STMT('const = consts.new_map("{0}")', const.dotted_fullname)
                    STMT('const["type"] = "{0}"', str(const.type))
                    STMT('const["value"] = "{0}"', const.value)
            SEP()
        SEP()
        with BLOCK("def ProcessorFactory(handler, exception_map = {})"):
            STMT("return lambda transport: Processor(transport, handler, exception_map)")
    
    def _generate_processor_function(self, module, func):
        BLOCK = module.block
        STMT = module.stmt
        SEP = module.sep
        
        if isinstance(func, compiler.Func):
            with BLOCK("def _func_{0}(args)", func.id):
                STMT("return handler.{0}(*args)", func.fullname)
        else:
            with BLOCK("def _func_{0}(args)", func.id):
                STMT("obj = args.pop(0)")
                if isinstance(func.origin, compiler.ClassAttr):
                    if func.type == compiler.t_void:
                        # setter
                        STMT("obj.{0} = args[0]", func.origin.name)
                    else:
                        # getter
                        STMT("return obj.{0}", func.origin.name)
                else:
                    STMT("return obj.{0}(*args)", func.origin.name)

    def _generate_processor_unpacker(self, module, func):
        BLOCK = module.block
        STMT = module.stmt
        SEP = module.sep
        
        with BLOCK("def _unpack_{0}()", func.id):
            if not func.args:
                STMT("return []")
                return 
            with BLOCK("return ", prefix = "[", suffix="]"):
                for arg in func.args:
                    STMT("{0}.unpack(self.transport),", type_to_packer(arg.type))
    
    def generate_client(self, module, service):
        BLOCK = module.block
        STMT = module.stmt
        SEP = module.sep

        with BLOCK("class Client(agnos.BaseClient)"):
            with BLOCK("def __init__(self, transport, checked)"):
                self.generate_client_ctor(module, service)
                SEP()
                with BLOCK("if checked"):
                    STMT("self.assert_service_compatibility()")
            SEP()
            for func in service.funcs.values():
                if not isinstance(func, compiler.Func) or func.namespace or not func.clientside:
                    continue
                args = ", ".join(arg.name for arg in func.args)
                with BLOCK("def {0}(_self, {1})", func.name, args):
                    STMT("return _self._funcs.sync_{0}({1})", func.id, args)
            SEP()
            self.generate_client_helpers(module, service)

    def generate_client_ctor(self, module, service):
        BLOCK = module.block
        STMT = module.stmt
        SEP = module.sep

        for rec in service.records_and_exceptions(is_complex_type):
            self.generate_record_packer(module, rec)
            SEP()
        STMT("packed_exceptions = {}")
        STMT("self._utils = agnos.ClientUtils(transport, packed_exceptions)")
        SEP()
        STMT("storer = lambda proxy: -1 if proxy is None else proxy._objref")
        for cls in service.classes():
            STMT("{0}ObjRef = packers.ObjRef({1}, storer, partial("
                "self._utils.get_proxy, {0}Proxy, self))", cls.name, cls.id)
        SEP()
        STMT("packers_map = {}")
        STMT("heteroMapPacker = packers.HeteroMapPacker(999, packers_map)")
        STMT("packers_map[999] = heteroMapPacker")
        SEP()
        self.generate_templated_packers(module, service)
        SEP()
        for exc in service.exceptions():
            STMT("packed_exceptions[{0}] = {1}", exc.id, type_to_packer(exc))
        SEP()
        for tp in service.types.values():
            STMT("packers_map[{0}] = {1}", tp.id, type_to_packer(tp))
        SEP()
        with BLOCK("class Functions(object)"):
            with BLOCK("def __init__(self, utils)"):
                STMT("self.utils = utils")
            for func in service.funcs.values():
                args = ", ".join(arg.name for arg in func.args)
                with BLOCK("def sync_{0}(_self, {1})", func.id, args):
                    with BLOCK("with _self.utils.invocation({0}, {1}) as seq", 
                            func.id, type_to_packer(func.type)):
                        if not func.args:
                            STMT("pass")
                        else:
                            for arg in func.args:
                                STMT("{0}.pack({1}, _self.utils.transport)", 
                                    type_to_packer(arg.type), arg.name)
                    STMT("return _self.utils.get_reply(seq)")
        SEP()
        STMT("self._funcs = Functions(self._utils)")
        SEP()
        namespaces1 = set(func.namespace.split(".")[0] for func in service.funcs.values() 
            if func.namespace)
        namespaces2 = set(const.namespace.split(".")[0] for const in service.consts.values() 
            if const.namespace)
        for ns in namespaces1 | namespaces2:
            STMT("self.{0} = agnos.Namespace()", ns.split(".")[0])
        for func in service.funcs.values():
            if not func.namespace or not func.clientside:
                continue
            head, tail = (func.namespace + "." + func.name).split(".", 1)
            STMT("self.{0}['{1}'] = self._funcs.sync_{2}", head, tail, func.id)        
        for const in service.consts.values():
            if not const.namespace:
                continue
            head, tail = (const.namespace + "." + const.name).split(".", 1)
            STMT("self.{0}['{1}'] = {2}", head, tail, const_to_python(const.type, const.value))        

    def generate_client_helpers(self, module, service):
        BLOCK = module.block
        STMT = module.stmt
        SEP = module.sep

        with BLOCK("def assert_service_compatibility(self)"):
            STMT("info = self.get_service_info(agnos.INFO_SERVICE)")
            
            with BLOCK('if info["AGNOS_PROTOCOL_VERSION"] != AGNOS_PROTOCOL_VERSION'):
                STMT('''raise agnos.WrongAgnosVersion("expected protocol '%s' found '%s'" % (AGNOS_PROTOCOL_VERSION, info["AGNOS_PROTOCOL_VERSION"]))''')
            with BLOCK('if info["SERVICE_NAME"] != "{0}"', service.name):
                STMT('''raise agnos.WrongServiceName("expected service '{0}', found '%s'" % (info["SERVICE_NAME"],))''', service.name)
            with BLOCK('if CLIENT_VERSION'):
                STMT('supported_versions = info.get("SUPPORTED_VERSIONS", None)')
                with BLOCK('if not supported_versions or CLIENT_VERSION not in supported_versions'):
                    STMT('''raise agnos.IncompatibleServiceVersion("server does not support client version '%s'" % (CLIENT_VERSION,))''')























