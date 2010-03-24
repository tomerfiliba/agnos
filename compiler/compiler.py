import xml.etree.ElementTree as etree


class IDLError(Exception):
    pass


def str_to_bool(text):
    text = text.lower()
    return text in ["true", "t", "yes", "y"] 


class Element(object):
    XML_TAG = None
    CHILDREN = []
    
    def __init__(self, attrib, members):
        pass
    
    @classmethod
    def load(cls, node):
        if node.tag != cls.XML_TAG:
            raise IDLError("expected 'service', not %r" % (node.tag,))

        mapping = dict((childclass.XML_TAG, childclass) for childclass in cls.CHILDREN)
        members = []
        for child in node:
            if child.tag not in mapping:
                raise IDLError("invalid element %r inside %r" % (child.tag, cls)) 
            members.append(mapping[child.tag].load(child))
        return cls(node.attrib, members)
    
    def resolve(self, service):
        if getattr(self, "_resolved", False):
            self._resolved = True
            self._resolve(service)
    def _resolve(self, service):
        if hasattr(self, "type"):
            self.type = service.get_type(self.type)


class EnumMember(Element):
    XML_TAG = "member"
    
    def __init__(self, attrib, members):
        self.name = attrib["name"]
        self.value = attrib.get("value", None)
    def fixate(self, value):
        if self.value is None:
            self.value = value
        return self.value

class Enum(Element):
    XML_TAG = "enum"
    CHILDREN = [EnumMember]

    def __init__(self, attrib, members):
        self.name = attrib["name"]
        self.members = members
    def _resolve(self, service):
        next = 0
        for member in self.members:
            next = member.fixate(next) + 1

class Typedef(Element):
    XML_TAG = "typedef"

    def __init__(self, attrib, members):
        self.name = attrib["name"]
        self.type = attrib["type"]

class RecordMember(Element):
    XML_TAG = "attr"
    
    def __init__(self, attrib, members):
        self.name = attrib["name"]
        self.type = attrib["type"]

class Record(Element):
    XML_TAG = "record"
    CHILDREN = [RecordMember]

    def __init__(self, attrib, members):
        self.name = attrib["name"]
        self.members = members
    def _resolve(self, service):
        for mem in self.members:
            mem.resolve(service)

class Exception(Record):
    XML_TAG = "exception"
    CHILDREN = [RecordMember]

    def __init__(self, attrib, members):
        self.name = attrib["name"]
        self.members = members
    def _resolve(self, service):
        for mem in self.members:
            mem.resolve(service)

class ClassAttr(Element):
    XML_TAG = "attr"

    def __init__(self, attrib, members):
        self.name = attrib["name"]
        self.type = attrib["type"]
        self.get = str_to_bool(attrib.get("get", "yes"))
        self.set = str_to_bool(attrib.get("set", "yes"))

class MethodArg(Element):
    XML_TAG = "arg"

    def __init__(self, attrib, members):
        self.name = attrib["name"]
        self.type = attrib["type"]

class ClassMethod(Element):
    XML_TAG = "method"
    CHILDREN = [MethodArg]

    def __init__(self, attrib, members):
        self.name = attrib["name"]
        self.type = attrib["type"]
        self.args = members

class Class(Element):
    XML_TAG = "class"
    CHILDREN = [ClassMethod, ClassAttr]
    
    def __init__(self, attrib, members):
        self.name = attrib["name"]
        self.attrs = [mem for mem in members if isinstance(mem, ClassAttr)]
        self.methods = [mem for mem in members if isinstance(mem, ClassMethod)]
    
    def _resolve(self, service):
        for attr in self.attrs:
            attr.resolve(service)
        for method in self.methods:
            method.resolve(service)

class FuncArg(Element):
    XML_TAG = "arg"
    
    def __init__(self, attrib, members):
        self.name = attrib["name"]
        self.type = attrib["type"]

class Func(Element):
    XML_TAG = "func"
    CHILDREN = [FuncArg]
    
    def __init__(self, attrib, members):
        self.name = attrib["name"]
        self.type = attrib["type"]
        self.args = members

class BuiltinType(object):
    def __init__(self, name):
        self.name = name
    def __repr__(self):
        return self.name
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

class ListType(BuiltinType):
    def __init__(self, oftype):
        self.oftype = oftype
    def __repr__(self):
        return "list<%r>" % (self.oftype,)

class MapType(BuiltinType):
    def __init__(self, keytype, valtype):
        self.keytype = keytype
        self.valtype = valtype
    def __repr__(self):
        return "map<%r, %r>" % (self.keytype, self.valtype)


class Service(Element):
    XML_TAG = "service"
    CHILDREN = [Typedef, Enum, Record, Exception, Class, Func]
    BUILTIN_TYPES = {
        "int8" : t_int8,
        "int16" : t_int16,
        "int32" : t_int32,
        "int64" : t_int64,
        "float" : t_float,
        "bool" : t_bool,
        "date" : t_date,
        "buffer" : t_buffer,
        "str" : t_string,
        "string" : t_string,
        "list" : None,
        "map" : None,
    }
    
    def __init__(self, attrib, members):
        self.name = attrib["name"]
        self.types = {}
        self.roots = {}
        self._resolved = False
        for mem in members:
            if isinstance(mem, (Func,)):
                if mem.name in self.roots:
                    raise IDLError("name %r already defined" % (mem.name,))
                self.roots[mem.name] = mem
            else:
                if mem.name in self.BUILTIN_TYPES:
                    raise IDLError("name %r is reserved" % (mem.name,))
                if mem.name in self.types:
                    raise IDLError("name %r already defined" % (mem.name,))
                self.types[mem.name] = mem
    
#    def _parse_template(self, stream):
#        name = ""
#        subs = []
#        while True:
#            ch = stream.read(1)
#            if not ch or ch == "," or ch == ">":
#                return name, subs
#            if ch == " \t":
#                pass
#            elif ch == "<":
#                while True:
#                    subs.append(self._parse_template(stream))
#            else:
#                name += ch
    
    def get_type(self, name):
        name = name.strip()
        if name == "list" or name == "map":
            raise IDLError("list or map require template")
        if "<" in name:
            raise IDLError("templates not yet supported")
        if name in self.BUILTIN_TYPES:
            return self.BUILTIN_TYPES[name]
        if name in self.types:
            return self.types[name]
        raise IDLError("unknown type %r" % (name,))
    
    @classmethod
    def from_file(cls, file):
        if hasattr(file, "read"):
            data = file.read()
        else:
            data = open(file, "r").read()
        xml = etree.fromstring(data)
        return cls.load(xml)
    
    def resolve(self):
        if self._resolved:
            return
        self._resolved = True
        for mem in self.types.values():
            mem.resolve(self.types)
        for mem in self.roots.values():
            mem.resolve(self.types)


def compile(filename, target):
    service = Service.from_file(filename)
    s.resolve()
    target.generate(service)


















