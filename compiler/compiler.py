import re
import hashlib
import xml.etree.ElementTree as etree
import itertools
from .idl import parse_const, parse_template, IDLError


ID_GENERATOR = itertools.count(900000)
AGNOS_VERSION = "AGNOS-1.0"

def is_complex_type(idltype):
    if isinstance(idltype, TList):
        return is_complex_type(idltype.oftype)
    elif isinstance(idltype, TMap):
        return is_complex_type(idltype.keytype) or is_complex_type(idltype.valtype)
    elif isinstance(idltype, Class):
        return True
    elif isinstance(idltype, Record):
        return any(is_complex_type(mem.type) for mem in idltype.members)
    else:
        return False


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
    # names must not begin with _
    first = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
    rest = first + "_0123456789"
    if v[0] not in first:
        raise IDLError("invalid identifier %r assigned to %r" % (v, name))
    for ch in v[1:]:
        if ch not in rest:
            raise IDLError("invalid identifier %r assigned to %r" % (v, name))
    return v

def TYPENAME(name, v):
    if not v:
        raise IDLError("required attribute %r missing" % (name,))
    first = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
    rest = first + "_0123456789["
    if v[0] not in first:
        raise IDLError("invalid identifier %r assigned to %r" % (v, name))
    seen_paren = False
    for ch in v[1:]:
        if ch == "[" and not seen_paren:
            seen_paren = True
            rest += "], "
        if ch not in rest:
            raise IDLError("invalid identifier %r assigned to %r" % (v, name))
    return v

def TYPENAME_NONVOID(name, v):
    v = TYPENAME(name, v)
    if v == "void":
        raise IDLError("argument or attribute type cannot be void: %r" % (name,))
    return v

def TYPENAME_COMMA_SEP(name, v):
    if not v:
        return []
    return [TYPENAME_NONVOID(name, tp) for tp in v.split(",")]

def COMMA_SEP(name, v):
    if not v:
        return []
    return [item.strip() for item in v.split(",")]


class Annotation(object):
    def __init__(self, name, value):
        self.name = name
        self.value = value
    def __str__(self):
        return "%s=%s"

class Element(object):
    XML_TAG = None
    CHILDREN = []
    ATTRS = {}
    
    def __init__(self, attrib, members, annotations):
        self._resolved = False
        self._postprocessed = False
        self.doc = attrib.pop("doc", "").strip()
        self.annotations = annotations
        if "id" in attrib:
            if "id" not in self.ATTRS:
                self.id = int(attrib.pop("id"))
        else:
            self.id = ID_GENERATOR.next()
        for name, checker in self.ATTRS.iteritems():
            try:
                value = checker(name, attrib.pop(name, None))
            except IDLError, ex:
                print ex
                print self.XML_TAG, attrib, members, annotations
                raise
            setattr(self, name, value)
        if attrib:
            raise IDLError("unknown attributes: %r" % (attrib.keys(),))
        self.build_members(members)
    
    def duplicate(self, **kwargs):
        e = Element.__new__(self.__class__)
        e.__dict__.update(self.__dict__)
        e._resolved = False
        e._postprocessed = False
        e.id = None
        for k, v in kwargs.iteritems():
            setattr(e, k, v)
        return e
    
    def __repr__(self):
        attrs = ["%s=%r" % (name, getattr(self, name, None)) for name in self.ATTRS.keys()]
        return "%s(%s)" % (self.__class__.__name__, ", ".join(sorted(attrs)))
    
    def build_members(self, members):
        if self.CHILDREN:
            self.members = members
    
    @classmethod
    def load(cls, node):
        if node.tag != cls.XML_TAG:
            raise IDLError("expected %r, not %r" % (cls.XML_TAG, node.tag,))

        mapping = dict((childclass.XML_TAG, childclass) for childclass in cls.CHILDREN)
        members = []
        annotations = []
        for child in node:
            if child.tag == "doc":
                if "doc" in node.attrib:
                    raise IDLError("doc for %r given more than once" % (node.tag,))
                node.attrib["doc"] = child.text
            elif child.tag == "annotation":
                annotations.append(Annotation(child.attrib["name"], child.attrib["value"]))
            elif child.tag not in mapping:
                raise IDLError("invalid element %r inside %r" % (child.tag, cls))
            else: 
                members.append(mapping[child.tag].load(child))
        return cls(node.attrib, members, annotations)
    
    def resolve(self, service):
        if self._resolved:
            return
        self._resolve(service)
        self._resolved = True
    def _resolve(self, service):
        if hasattr(self, "type"):
            self.type = service.get_type(self.type)
    
    def postprocess(self, service):
        if self._postprocessed:
            return
        if self.id is not None:
            if self.id in service.known_ids:
                raise IDLError("duplicate element ID: %r" % (self.id,))
            service.known_ids.add(self.id)
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
    ATTRS = dict(name = IDENTIFIER, type = TYPENAME_NONVOID)

class Const(Element):
    XML_TAG = "const"
    ATTRS = dict(name = IDENTIFIER, type = TYPENAME_NONVOID, value = REQUIRED, namespace = DEFAULT(None))
    
    def _resolve(self, service):
        Element._resolve(self, service)
        self.value = parse_const(self.value)

    @property
    def dotted_fullname(self):
        if self.namespace:
            return self.namespace + "." + self.name
        else:
            return self.name


class RecordMember(Element):
    XML_TAG = "attr"
    ATTRS = dict(name = IDENTIFIER, type = TYPENAME_NONVOID)

class Record(Element):
    XML_TAG = "record"
    CHILDREN = [RecordMember]
    ATTRS = dict(name = IDENTIFIER, extends = TYPENAME_COMMA_SEP)

    def stringify(self):
        return self.name
    
    def __str__(self):
        return self.name

    def get_complex_types(self):
        return sorted(
            set(mem.type for mem in self.members if is_complex_type(mem.type)),
            key = lambda tp: tp.stringify())

    def _resolve(self, service):
        names = set()
        members = []
        
        self.extends = [service.get_type(tp) for tp in self.extends]
        for rec in self.extends:
            if not isinstance(rec, Record):
                raise IDLError("record %r extends %r, which is not a record itself" % (self.name, rec))
            rec.resolve(service)
            for mem in rec.members:
                members.append(mem)
                if mem.name in names:
                    raise IDLError("%s: name %r is redefined by %r" % (self.name, mem.name, rec.name))
                names.add(mem.name)
        for mem in self.members:
            mem.resolve(service)
            if mem.name in names:
                raise IDLError("name %r is redefined by %r" % (mem.name, self.name))
            members.append(mem)
        self.members = members

class Exception(Record):
    XML_TAG = "exception"

class ClassAttr(Element):
    XML_TAG = "attr"
    ATTRS = dict(name = IDENTIFIER, type = TYPENAME_NONVOID, 
        get = STR_TO_BOOL(True), set = STR_TO_BOOL(True), 
        getid = DEFAULT(None), setid = DEFAULT(None))
    
    def build_members(self, members):
        self.getter = None
        self.setter = None
        self.id = None
        if self.getid is None:
            self.getid = ID_GENERATOR.next()
        if self.setid is None:
            self.setid = ID_GENERATOR.next()
    
    def _postprocess(self, service):
        if self.getid in service.known_ids:
            raise IDLError("duplicate element ID: %r" % (self.getid,))
        service.known_ids.add(self.getid)
        if self.setid in service.known_ids:
            raise IDLError("duplicate element ID: %r" % (self.setid,))
        service.known_ids.add(self.setid)

class MethodArg(Element):
    XML_TAG = "arg"
    ATTRS = dict(name = IDENTIFIER, type = TYPENAME_NONVOID)

class ClassMethod(Element):
    XML_TAG = "method"
    CHILDREN = [MethodArg]
    ATTRS = dict(name = IDENTIFIER, type = TYPENAME, clientside = STR_TO_BOOL(True))

    def build_members(self, members):
        self.args = members
        self.func = None
    
    def _resolve(self, service):
        self.type = service.get_type(self.type)
        for arg in self.args:
            arg.resolve(service)

class InheritedAttr(Element):
    XML_TAG = "inherited-attr"
    ATTRS = dict(name = IDENTIFIER, getid = DEFAULT(None), setid = DEFAULT(None))
    
class InheritedMethod(Element):
    XML_TAG = "inherited-method"
    ATTRS = dict(name = IDENTIFIER, id = REQUIRED)


class Class(Element):
    XML_TAG = "class"
    CHILDREN = [ClassMethod, ClassAttr, InheritedMethod, InheritedAttr]
    ATTRS = dict(name = IDENTIFIER, extends = TYPENAME_COMMA_SEP)
    
    def stringify(self):
        return self.name
    
    def __str__(self):
        return self.name
    
    def build_members(self, members):
        self.attrs = [mem for mem in members if isinstance(mem, ClassAttr)]
        self.methods = [mem for mem in members if isinstance(mem, ClassMethod)]
        self.inherited_attrs = {}
        self.inherited_methods = {}
        for mem in members:
            if mem.name in self.inherited_methods or mem.name in self.inherited_attrs:
                if mem.name in self.inherited_attrs:
                    raise IDLError("inherited-attr %r already given" % (mem.name,))
                self.inherited_attrs[mem.name] = (mem.getid, mem.setid)
            elif isinstance(mem, InheritedMethod):
                if mem.name in self.inherited_methods or mem.name in self.inherited_attrs:
                    raise IDLError("inherited-method %r already given" % (mem.name,))
                self.inherited_methods[mem.name] = int(mem.id)
    
    def autogen(self, service, origin, name, type, id, *args):
        if name in service.funcs:
            raise IDLError("special name %s already in use" % (name,))
        func = AutoGeneratedFunc(origin, name, type, id, args)
        service.funcs[name] = func
        return func
    
    def get_id(self, name, which = None):
        if name in self.inherited_methods:
            return self.inherited_methods[name]
        elif name in self.inherited_attrs:
            i = ["get", "set"].index(which)
            return self.inherited_attrs[name][0]
        else:
            return ID_GENERATOR.next()
    
    def _resolve(self, service):
        names = set()
        self.extends = [service.get_type(tp) for tp in self.extends]
        self.all_attrs = []
        self.all_methods = []
        self.all_derived = set()
        
        for cls in self.extends:
            if not isinstance(cls, Class):
                raise IDLError("class %r extends %r, which is not a class itself" % (self.name, cls))
            cls.resolve(service)
            
            for mem in cls.all_attrs:
                self.all_attrs.append(mem.duplicate(getid = self.get_id(mem.name, "get"), setid = self.get_id(mem.name, "set")))
                if mem.name in names:
                    raise IDLError("name %r in %s is redefined by %r" % (mem.name, self.name, cls.name))
                names.add(mem.name)
            
            for mem in cls.all_methods:
                self.all_methods.append(mem.duplicate(id = self.get_id(mem.name)))
                if mem.name in names:
                    raise IDLError("name %r in %s is redefined by %r" % (mem.name, self.name, cls.name))
                names.add(mem.name)
        
        for mem in self.attrs:
            mem.resolve(service)
            if mem.name in names:
                raise IDLError("name %r is redefined by %r" % (mem.name, self.name))
            self.all_attrs.append(mem.duplicate(getid = self.get_id(mem.name, "get"), setid = self.get_id(mem.name, "set")))
        
        for mem in self.methods:
            mem.resolve(service)
            if mem.name in names:
                raise IDLError("name %r is redefined by %r" % (mem.name, self.name))
            self.all_methods.append(mem.duplicate(id = self.get_id(mem.name)))
    
    def _postprocess(self, service): 
        for attr in self.all_attrs:
            attr.parent = self 
            if attr.get:
                assert not attr.getter
                attr.getter = self.autogen(service, attr, "_%s_get_%s" % (self.name, attr.name), 
                    attr.type, attr.getid, ("_proxy", self))
            if attr.set:
                assert not attr.setter
                attr.setter = self.autogen(service, attr, "_%s_set_%s" % (self.name, attr.name), 
                    t_void, attr.setid, ("_proxy", self), ("value", attr.type))
        for method in self.all_methods:
            method.parent = self
            assert not method.func
            method.func = self.autogen(service, method, "_%s_%s" % (self.name, method.name), 
                method.type, method.id, ("_proxy", self), *[(arg.name, arg.type) for arg in method.args])
        self.parent = self
        self.all_bases = self._get_bases()
        for base in self.all_bases:
            base.all_derived.add(self)
    
    def _get_bases(self):
        bases = set(self.extends)
        for tp in self.extends:
            bases.update(tp._get_bases())
        return bases

class FuncArg(Element):
    XML_TAG = "arg"
    ATTRS = dict(name = IDENTIFIER, type = TYPENAME_NONVOID)

class Func(Element):
    XML_TAG = "func"
    CHILDREN = [FuncArg]
    ATTRS = dict(name = IDENTIFIER, type = TYPENAME, namespace = DEFAULT(None),
        clientside = STR_TO_BOOL(True))

    def build_members(self, members):
        self.args = members

    @property
    def fullname(self):
        if self.namespace:
            return self.namespace.replace(".", "_") + "_" + self.name
        else:
            return self.name

    @property
    def dotted_fullname(self):
        if self.namespace:
            return self.namespace + "." + self.name
        else:
            return self.name

    def _resolve(self, service):
        self.type = service.get_type(self.type)
        for arg in self.args:
            arg.resolve(service)

class AutoGeneratedFuncArg(object):
    def __init__(self, name, type):
        assert type != t_void
        self.name = name
        self.type = type

class AutoGeneratedFunc(object):
    def __init__(self, origin, name, type, id, args):
        self.origin = origin
        self.name = name
        self.type = type
        self.args = [AutoGeneratedFuncArg(arg[0], arg[1]) for arg in args]
        if id is None:
            self.id = ID_GENERATOR.next()
        else:
            self.id = id
        self.namespace = None
        
    @property
    def clientside(self):
        return self.origin.clientside
    
    @property
    def annotations(self):
        return self.origin.annotations
    
    @property
    def fullname(self):
        if self.namespace:
            return self.namespace.replace(".", "_") + "_" + self.name
        else:
            return self.name
    
    @property
    def dotted_fullname(self):
        if self.namespace:
            return self.namespace + "." + self.name
        else:
            return self.name

class BuiltinType(object):
    def __init__(self, id, name):
        self.id = id
        self.name = name
    def __repr__(self):
        return "BuiltinType(%s)" % (self.name,)
    def __str__(self):
        return self.name
    def __hash__(self):
        return self.id
    def __eq__(self, other):
        return self.id == other.id
    def __ne__(self, other):
        return not (self == other)
    def resolve(self, service):
        pass
    def stringify(self):
        return self.name

t_int8 = BuiltinType(1, "int8")
t_bool = BuiltinType(2, "bool")
t_int16 = BuiltinType(3, "int16")
t_int32 = BuiltinType(4, "int32")
t_int64 = BuiltinType(5, "int64")
t_float = BuiltinType(6, "float")
t_buffer = BuiltinType(7, "buffer")
t_date = BuiltinType(8, "date")
t_string = BuiltinType(9, "str")
t_void = BuiltinType(None, "void")
t_heteromap = BuiltinType(999, "heteromap")


def memoized(func):
    cache = {}
    def wrapper(*args):
        if args in cache:
            return cache[args]
        res = func(*args)
        cache[args] = res
        return res
    return wrapper

class TList(BuiltinType):
    def __init__(self, oftype):
        if oftype == t_void:
            raise IDLError("list: contained type cannot be 'void'")
        self.oftype = oftype
        self.id = ID_GENERATOR.next()
    @staticmethod
    @memoized
    def create(oftype):
        return TList(oftype)
    def __repr__(self):
        return "BuiltinType(list<%r>)" % (self.oftype,)
    def __str__(self):
        return "list[%s]" % (self.oftype,)
    def stringify(self):
        return "list_%s" % (self.oftype.stringify(),)

class TSet(BuiltinType):
    def __init__(self, oftype):
        if oftype == t_void:
            raise IDLError("set: contained type cannot be 'void'")
        self.oftype = oftype
        self.id = ID_GENERATOR.next()
    @staticmethod
    @memoized
    def create(oftype):
        return TSet(oftype)
    def __repr__(self):
        return "BuiltinType(set<%r>)" % (self.oftype,)
    def __str__(self):
        return "set[%s]" % (self.oftype,)
    def stringify(self):
        return "set_%s" % (self.oftype.stringify(),)

class TMap(BuiltinType):
    def __init__(self, keytype, valtype):
        if keytype == t_void:
            raise IDLError("map: key type cannot be 'void'")
        if valtype == t_void:
            raise IDLError("map: value type cannot be 'void'")
        self.keytype = keytype
        self.valtype = valtype
        self.id = ID_GENERATOR.next()
    @staticmethod
    @memoized
    def create(keytype, valtype):
        return TMap(keytype, valtype)
    def __repr__(self):
        return "BuiltinType(map<%r, %r>)" % (self.keytype, self.valtype)
    def __str__(self):
        return "map[%s, %s]" % (self.keytype, self.valtype)
    def stringify(self):
        return "map_%s_%s" % (self.keytype.stringify(), self.valtype.stringify())

class TRefList(BuiltinType):
    def __init__(self, oftype):
        if oftype == t_void:
            raise IDLError("reflist: contained type cannot be 'void'")
        self.oftype = oftype
        self.id = ID_GENERATOR.next()
    @staticmethod
    @memoized
    def create(oftype):
        return TList(oftype)
    def __repr__(self):
        return "BuiltinType(reflist<%r>)" % (self.oftype,)
    def __str__(self):
        return "reflist[%s]" % (self.oftype,)
    def stringify(self):
        return "reflist_%s" % (self.oftype.stringify(),)

class TRefMap(BuiltinType):
    def __init__(self, keytype, valtype):
        if keytype == t_void:
            raise IDLError("refmap: key type cannot be 'void'")
        if valtype == t_void:
            raise IDLError("refmap: value type cannot be 'void'")
        self.keytype = keytype
        self.valtype = valtype
        self.id = ID_GENERATOR.next()
    @staticmethod
    @memoized
    def create(keytype, valtype):
        return TMap(keytype, valtype)
    def __repr__(self):
        return "BuiltinType(refmap<%r, %r>)" % (self.keytype, self.valtype)
    def __str__(self):
        return "refmap[%s, %s]" % (self.keytype, self.valtype)
    def stringify(self):
        return "refmap_%s_%s" % (self.keytype.stringify(), self.valtype.stringify())

pattern = re.compile(' *\<!-- *INCLUDE *"([^"]+)" *--\>')

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
    ATTRS = dict(name = IDENTIFIER, package = DEFAULT(None), versions = COMMA_SEP, 
        clientversion = DEFAULT(None))
    BUILTIN_TYPES = {
        "void" : t_void,
        "int8" : t_int8,
        "int16" : t_int16,
        "int32" : t_int32,
        "int" : t_int32,
        "int64" : t_int64,
        "float" : t_float,
        "bool" : t_bool,
        "date" : t_date,
        "buffer" : t_buffer,
        "str" : t_string,
        "string" : t_string,
        "heteromap" : t_heteromap,
        "heterodict" : t_heteromap,
        "hmap" : t_heteromap,
        "hdict" : t_heteromap,
        "list" : None,
        "set" : None,
        "map" : None,
        "dict" : None,
        "reflist" : None,
        "rlist" : None,
        "refmap" : None,
        "refdict" : None,
        "rmap" : None,
        "rdict" : None,
    }
    
    def build_members(self, members):
        self.members = members
        self.all_types = []
        self.types = {}
        self.funcs = {}
        self.consts = {}
        self.known_ids = set()
        self._resolved = False
        if not self.clientversion:
            if self.versions:
                self.clientversion = self.versions[-1]
            else:
                self.clientversion = None
        if not self.package:
            self.package = self.name
        for mem in members:
            if isinstance(mem, Func):
                if mem.dotted_fullname in self.funcs:
                    raise IDLError("func %r already defined" % (mem.dotted_fullname,))
                self.funcs[mem.dotted_fullname] = mem
            elif isinstance(mem, Const):
                if mem.dotted_fullname in self.consts:
                    raise IDLError("const %r already defined" % (mem.dotted_fullname,))
                self.consts[mem.dotted_fullname] = mem
            else:
                if mem.name in self.BUILTIN_TYPES:
                    raise IDLError("type name %r is reserved" % (mem.name,))
                if mem.name in self.types:
                    raise IDLError("type name %r already defined" % (mem.name,))
                self.types[mem.name] = mem
    
    def get_type(self, text):
        head, children = parse_template(text)
        tp = self._get_type(head, children)
        if tp not in self.all_types:
            self.all_types.append(tp)
        return tp
    
    def _get_type(self, head, children):
        if head == "list":
            if len(children) != 1:
                raise IDLError("list template: wrong number of parameters: %r" % (text,))
            head2, children2 = children[0]
            tp = self._get_type(head2, children2)
            return TList.create(tp)
        elif head == "set":
            if len(children) != 1:
                raise IDLError("set template: wrong number of parameters: %r" % (text,))
            head2, children2 = children[0]
            tp = self._get_type(head2, children2)
            return TSet.create(tp)
        elif head == "map" or head == "dict":
            if len(children) != 2:
                raise IDLError("map template: wrong number of parameters: %r" % (text,))
            khead, kchildren = children[0]
            vhead, vchildren = children[1]
            ktp = self._get_type(khead, kchildren)
            vtp = self._get_type(vhead, vchildren)
            return TMap.create(ktp, vtp)
        elif head == "reflist" or head == "rlist":
            if len(children) != 1:
                raise IDLError("reflist template: wrong number of parameters: %r" % (text,))
            head2, children2 = children[0]
            tp = self._get_type(head2, children2)
            return TRefList.create(tp)
        elif head == "refmap" or head == "refdict" or head == "rmap" or head == "rdict":
            if len(children) != 2:
                raise IDLError("refmap template: wrong number of parameters: %r" % (text,))
            khead, kchildren = children[0]
            vhead, vchildren = children[1]
            ktp = self._get_type(khead, kchildren)
            vtp = self._get_type(vhead, vchildren)
            return TRefMap.create(ktp, vtp)
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
        sha1 = hashlib.sha1(data)
        xml = etree.fromstring(data)
        inst = cls.load(xml)
        inst.digest = sha1.hexdigest()
        return inst
    
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







