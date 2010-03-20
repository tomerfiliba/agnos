from struct import Struct as _BuiltinStruct


class Datatype(object):
    __slots__ = []
    def pack(self, obj, stream):
        raise NotImplementedError()
    def unpack(self, stream):
        raise NotImplementedError()

class PrimitiveDatatype(Datatype):
    __slots__ = ["format"]
    def __init__(self, format):
        self.format = _BuiltinStruct(format)
    def pack(self, obj, stream):
        data = self.format.pack(obj)
        stream.write(data)
    def unpack(self, stream):
        return self.format.unpack(stream.read(self.format.size))[0]

Int8 = PrimitiveDatatype("!b")
Int16 = PrimitiveDatatype("!h")
Int32 = PrimitiveDatatype("!l")
Int64 = PrimitiveDatatype("!q")
ObjRef = Int64
Float = PrimitiveDatatype("!d")

class Bool_(PrimitiveDatatype):
    __slots__ = []
    def pack(self, obj, stream):
        PrimitiveDatatype.pack(int(obj), stream)
    def unpack(self, stream):
        return bool(PrimitiveDatatype.unpack(stream))

Bool = Bool_("!b")

class Bytes_(Datatype):
    __slots__ = []
    def pack(self, obj, stream):
        Int32.pack(len(obj), stream)
        stream.write(obj)
    def unpack(self, stream):
        length = Int32.unpack(stream)
        return stream.read(length)

class String_(Bytes_):
    __slots__ = []
    def pack(self, obj, stream):
        Bytes_.pack(self, obj.encode("utf8"), stream)
    def unpack(self, obj, stream):
        return Bytes_.unpack(self, stream).decode("utf8")

Bytes = Bytes_()
String = String_()

class List(Datatype):
    __slots__ = ["oftype"]
    def __init__(self, oftype):
        self.oftype = oftype
    def pack(self, obj, stream):
        Int32.pack(len(obj), stream)
        for subobj in obj:
            self.oftype.pack(subobj, stream)
    def unpack(self, stream):
        length = Int32.unpack(stream)
        result = []
        for i in xrange(length):
            subobj = self.oftype.unpack(stream)
            result.append(subobj)
        return result

class Map(Datatype):
    __slots__ = ["keytype", "valtype"]
    def __init__(self, keytype, valtype):
        self.keytype = keytype
        self.valtype = valtype
    def pack(self, obj, stream):
        Int32.pack(len(obj), stream)
        for k, v in obj.iteritems():
            self.keytype.pack(k, stream)
            self.keytype.pack(v, stream)
    def unpack(self, stream):
        length = Int32.unpack(stream)
        result = {}
        for i in xrange(length):
            key = self.keytype.unpack(stream)
            val = self.valtype.unpack(stream)
            result[key] = val
        return result

class StructMember(object):
    __slots__ = ["name", "type", "value"]
    def __init__(self, name, type, value = None):
        self.name = name
        self.type = type
        self.value = value

class Record(Datatype):
    __slots__ = ["members"]
    def __init__(self, members):
        self.members = members
    def pack(self, obj, stream):
        for mem in self.members:
            val = getattr(obj, mem.name)
            mem.type.pack(val, stream)
    def unpack(self, stream):
        obj = {}
        for mem in self.members:
            val = mem.type.unpack(stream)
            obj[mem.name] = val
        return obj

"""
record Person:
    name as string
    id as int32
    //List<Person> parents
"""

class Person(object):
    _datatype = Record([
        StructMember("name", String), 
        StructMember("id", Int32)
    ])
    
    def __init__(self, name = None, id = 0):
        self.name = name
        self.id = id
    
    def __repr__(self):
        return "Person(name = %r, id = %r)" % (self.name, self.id)
    
    def pack(self, stream):
        self._datatype.pack(self, stream)

    @classmethod    
    def unpack(cls, stream):
        members = cls._datatype.unpack(stream)
        return cls(**members)

"""
class File:
    readonly attr filename as string
    method new(filename as string, mode as string = "r")
    method read(count as int32) as bytes
    method write(data as bytes)
"""

class FileProxy(object):
    __slots__ = ["_client", "_objref"]
    def __init__(self, client, objref):
        self._client = client
        self._objref = objref
    
    def __repr__(self):
        return "FileProxy(%r, %r)" % (self._client, self._objref)
    
    def _get_filename(self):
        return self._client._File_filename_getter(self._objref)
    filename = property(_get_filename)
    
    def read(self, count):
        return self._client._File_read(count)
    
    def write(self, data):
        self._client._File_write(data)


























