import re
import xml.etree.ElementTree as etree
import itertools
from .idl import parse_const, parse_template, IDLError


ID_GENERATOR = itertools.count(1337)

def DEFAULT(default):
    def checker(name, v):
        return v if v else default
    return checker

def REQUIRED(name, v):
    if not v:
        raise IDLError("required argument %r missing" % (name,))
    return v

def STR_TO_BOOL(default):
    def checker(name, text):
        if not text:
            return default
        return text.lower() in ["true", "t", "yes", "y"]
    return checker

def IDENTIFIER(name, v):
    if not v:
        raise IDLError("required attribute %r missing" % (name,))
    first = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_"
    rest = first + "0123456789"
    if v[0] not in first:
        raise IDLError("invalid identifier %r assigned to %r" % (v, name))
    for ch in v[1:]:
        if ch not in rest:
            raise IDLError("invalid identifier %r assigned to %r" % (v, name))
    return v

class Element(object):
    XML_TAG = None
    CHILDREN = []
    ATTRS = {}
    
    def __init__(self, attrib, members):
        self._resolved = False
        self._postprocessed = False
        self.doc = attrib.pop("doc", "").strip()
        for name, checker in self.ATTRS.iteritems():
            value = checker(name, attrib.pop(name, None)) 
            setattr(self, name, value)
        if attrib:
            raise IDLError("unknown attributes: %r" % (attrib.keys(),))
        self.build_members(members)
        self.id = ID_GENERATOR.next()
    
    def build_members(self, members):
        if self.CHILDREN:
            self.members = members
    
    @classmethod
    def load(cls, node):
        if node.tag != cls.XML_TAG:
            raise IDLError("expected %r, not %r" % (cls.XML_TAG, node.tag,))

        mapping = dict((childclass.XML_TAG, childclass) for childclass in cls.CHILDREN)
        members = []
        for child in node:
            if child.tag == "doc":
                if "doc" in node.attrib:
                    raise IDLError("doc for %r given more than once" % (node.tag,))
                node.attrib["doc"] = child.text
            elif child.tag not in mapping:
                raise IDLError("invalid element %r inside %r" % (child.tag, cls))
            else: 
                members.append(mapping[child.tag].load(child))
        return cls(node.attrib, members)
    
    def resolve(self, service):
        if not self._resolved:
            self._resolve(service)
            self._resolved = True
    def _resolve(self, service):
        if hasattr(self, "type"):
            self.type = service.get_type(self.type)
    
    def postprocess(self, service):
        if not self._postprocessed:
            self._postprocess(service)
            self._postprocessed = True
    
    def _postprocess(self, service):
        pass

class EnumMember(Element):
    XML_TAG = "member"
    ATTRS = dict(name = IDENTIFIER, value = DEFAULT(None))
    
    def fixate(self, value):
        if self.value is None:
            self.value = value
        else:
            self.value = parse_const(self.value)
        return self.value

class Enum(Element):
    XML_TAG = "enum"
    CHILDREN = [EnumMember]
    ATTRS = dict(name = IDENTIFIER)

    def _resolve(self, service):
        next = 0
        names = set()
        for member in self.members:
            if member.name in names:
                raise IDLError("enum member %r already defined" % (member.name,))
            names.add(member.name)
            next = member.fixate(next) + 1

class Typedef(Element):
    XML_TAG = "typedef"
    ATTRS = dict(name = IDENTIFIER, type = IDENTIFIER)

class Const(Element):
    XML_TAG = "const"
    ATTRS = dict(name = IDENTIFIER, type = IDENTIFIER, value = REQUIRED)
    
    def _resolve(self, service):
        Element._resolve(self, service)
        self.value = parse_const(self.value)

class RecordMember(Element):
    XML_TAG = "attr"
    ATTRS = dict(name = IDENTIFIER, type = IDENTIFIER)

class Record(Element):
    XML_TAG = "record"
    CHILDREN = [RecordMember]
    ATTRS = dict(name = IDENTIFIER)

    def _resolve(self, service):
        for mem in self.members:
            mem.resolve(service)

class Exception(Record):
    XML_TAG = "exception"

class ClassAttr(Element):
    XML_TAG = "attr"
    ATTRS = dict(name = IDENTIFIER, type = IDENTIFIER, get = STR_TO_BOOL(True), set = STR_TO_BOOL(True))

class MethodArg(Element):
    XML_TAG = "arg"
    ATTRS = dict(name = IDENTIFIER, type = IDENTIFIER)

class ClassMethod(Element):
    XML_TAG = "method"
    CHILDREN = [MethodArg]
    ATTRS = dict(name = IDENTIFIER, type = IDENTIFIER)

    def build_members(self, members):
        self.args = members
    
    def _resolve(self, service):
        self.type = service.get_type(self.type)
        for arg in self.args:
            arg.resolve(service)

class ClassCtor(Element):
    XML_TAG = "ctor"
    CHILDREN = [MethodArg]

    def build_members(self, members):
        self.args = members
    
    def _resolve(self, service):
        for arg in self.args:
            arg.resolve(service)

class Class(Element):
    XML_TAG = "class"
    CHILDREN = [ClassMethod, ClassAttr] # ClassCtor]
    ATTRS = dict(name = IDENTIFIER)
    
    def build_members(self, members):
        self.attrs = [mem for mem in members if isinstance(mem, ClassAttr)]
        self.methods = [mem for mem in members if isinstance(mem, ClassMethod)]
        ctors = [mem for mem in members if isinstance(mem, ClassCtor)]
        if not ctors:
            self.ctor = None
        elif len(ctors) == 1:
            self.ctor = ctors[0]
        else:
            raise IDLError("only one class constructor for %r may be defined" % (self.name,))
    
    def autogen(self, service, origin, name, type, *args):
        if name in service.funcs:
            raise IDLError("special name %s already in use" % (name,))
        service.funcs[name] = AutoGeneratedFunc(origin, name, type, args)
    
    def _resolve(self, service):
        for attr in self.attrs:
            attr.resolve(service)
        for method in self.methods:
            method.resolve(service)
        if self.ctor:
            self.ctor.resolve(service)
    
    def _postprocess(self, service): 
        for attr in self.attrs:
            attr.parent = self 
            if attr.get:
                self.autogen(service, attr, "_%s_get_%s" % (self.name, attr.name), attr.type, ("_proxy", self))
            if attr.set:
                self.autogen(service, attr, "_%s_set_%s" % (self.name, attr.name), t_void, ("_proxy", self), ("value", attr.type))
        for method in self.methods:
            method.parent = self 
            self.autogen(service, method, "_%s_%s" % (self.name, method.name), method.type, ("_proxy", self), *[(arg.name, arg.type) for arg in method.args])
        self.parent = self
        if self.ctor:
            self.autogen(service, self, self.name, self, *[(arg.name, arg.type) for arg in self.ctor.args])

class FuncArg(Element):
    XML_TAG = "arg"
    ATTRS = dict(name = IDENTIFIER, type = IDENTIFIER)

class Func(Element):
    XML_TAG = "func"
    CHILDREN = [FuncArg]
    ATTRS = dict(name = IDENTIFIER, type = IDENTIFIER)

    def build_members(self, members):
        self.args = members

    def _resolve(self, service):
        self.type = service.get_type(self.type)
        for arg in self.args:
            arg.resolve(service)

class AutoGeneratedFuncArg(object):
    def __init__(self, name, type):
        self.name = name
        self.type = type

class AutoGeneratedFunc(object):
    def __init__(self, origin, name, type, args):
        self.origin = origin
        self.name = name
        self.type = type
        self.args = [AutoGeneratedFuncArg(arg[0], arg[1]) for arg in args]
        self.id = ID_GENERATOR.next()

class BuiltinType(object):
    def __init__(self, name):
        self.name = name
    def __repr__(self):
        return "BuiltinType(%s)" % (self.name,)
    def resolve(self, service):
        pass

t_int8 = BuiltinType("int8")
t_int16 = BuiltinType("int16")
t_int32 = BuiltinType("int32")
t_int64 = BuiltinType("int64")
t_float = BuiltinType("float")
t_bool = BuiltinType("bool")
t_date = BuiltinType("date")
t_buffer = BuiltinType("buffer")
t_string = BuiltinType("str")
t_void = BuiltinType("void")
t_objref = BuiltinType("objref")


class TList(BuiltinType):
    def __init__(self, oftype):
        self.oftype = oftype
    def __repr__(self):
        return "BuiltinType(list<%r>)" % (self.oftype,)

class TMap(BuiltinType):
    def __init__(self, keytype, valtype):
        self.keytype = keytype
        self.valtype = valtype
    def __repr__(self):
        return "BuiltinType(map<%r, %r>)" % (self.keytype, self.valtype)


pattern = re.compile(' *\<INCLUDE *filename *= *"([^"]+)" */\>')

def _load_file_with_includes(file):
    if hasattr(file, "read"):
        data = file.read()
    else:
        data = open(file, "r").read()
    newlines = []
    for line in data.splitlines():
        mo = pattern.match(line)
        if mo:
            fn = mo.groups()[0]
            newlines.extend(_load_file_with_includes(fn))
        else:
            newlines.append(line)
    return "\n".join(newlines)

class Service(Element):
    XML_TAG = "service"
    CHILDREN = [Typedef, Const, Enum, Record, Exception, Class, Func]
    ATTRS = dict(name = IDENTIFIER)
    BUILTIN_TYPES = {
        "void" : t_void,
        "int8" : t_int8,
        "int16" : t_int16,
        "int32" : t_int32,
        "int64" : t_int64,
        "float" : t_float,
        "bool" : t_bool,
        "date" : t_date,
        "buffer" : t_buffer,
        "str" : t_string,
        "objref" : t_objref,
        "string" : t_string,
        "list" : None,
        "map" : None,
        "dict" : None,
    }
    
    def build_members(self, members):
        self.members = members
        self.types = {}
        self.funcs = {}
        self.consts = {}
        self._resolved = False
        for mem in members:
            if isinstance(mem, Func):
                if mem.name in self.funcs:
                    raise IDLError("func %r already defined" % (mem.name,))
                self.funcs[mem.name] = mem
            if isinstance(mem, Const):
                if mem.name in self.consts:
                    raise IDLError("const %r already defined" % (mem.name,))
                self.consts[mem.name] = mem
            else:
                if mem.name in self.BUILTIN_TYPES:
                    raise IDLError("type name %r is reserved" % (mem.name,))
                if mem.name in self.types:
                    raise IDLError("type name %r already defined" % (mem.name,))
                self.types[mem.name] = mem
    
    def get_type(self, text):
        head, children = parse_template(text)
        return self._get_type(head, children)
    
    def _get_type(self, head, children):
        if head == "list":
            if len(children) != 1:
                raise IDLError("list template: wrong number of parameters: %r" % (text,))
            head2, children2 = children[0]
            tp = self._get_type(head2, children2)
            return TList(tp)
        elif head == "map" or head == "dict":
            if len(children) != 2:
                raise IDLError("map template: wrong number of parameters: %r" % (text,))
            khead, kchildren = children[0]
            vhead, vchildren = children[1]
            ktp = self._get_type(khead, kchildren)
            vtp = self._get_type(vhead, vchildren)
            return TList(ktp, vtp)
        elif head in self.BUILTIN_TYPES:
            return self.BUILTIN_TYPES[head]
        elif head in self.types:
            tp = self.types[head]
            if isinstance(tp, Typedef):
                tp.resolve(self)
                return tp.type
            else:
                return tp
        else:
            raise IDLError("unknown type %r" % (head,))
    
    @classmethod
    def from_file(cls, file):
        data = _load_file_with_includes(file)
        xml = etree.fromstring(data)
        return cls.load(xml)
    
    def resolve(self):
        if self._resolved:
            return
        self._resolved = True
        for mem in self.types.values():
            mem.resolve(self)
        for mem in self.funcs.values():
            mem.resolve(self)
        for mem in self.consts.values():
            mem.resolve(self)
        for mem in self.types.values():
            mem.postprocess(self)



def load_spec(filename):
    service = Service.from_file(filename)
    service.resolve()
    return service

def compile(filename, target):
    service = load_spec(filename)
    target.generate(service)







