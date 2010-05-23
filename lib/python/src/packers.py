from struct import Struct as _Struct
from datetime import datetime
import time


class Packer(object):
    __slots__ = []
    def pack(self, obj, stream):
        raise NotImplementedError()
    def unpack(self, stream):
        raise NotImplementedError()

class PrimitivePacker(Packer):
    __slots__ = ["struct"]
    def __init__(self, fmt):
        self.struct = _Struct(fmt)
    def pack(self, obj, stream):
        if obj is None:
            obj = 0
        stream.write(self.struct.pack(obj))
    def unpack(self, stream):
        return self.struct.unpack(stream.read(self.struct.size))[0]

Int8 = PrimitivePacker("!b")
Int16 = PrimitivePacker("!h")
Int32 = PrimitivePacker("!l")
Int64 = PrimitivePacker("!q")
Float = PrimitivePacker("!d")

class Bool(Packer):
    __slots__ = []
    @classmethod
    def pack(cls, obj, stream):
        if obj is None:
            obj = 0
        Int8.pack(int(obj), stream)
    @classmethod
    def unpack(cls, stream):
        return bool(Int8.unpack(stream))

class ObjRef(Packer):
    __slots__ = ["storer", "loader"]
    def __init__(self, storer, loader):
        self.storer = storer
        self.loader = loader
    def pack(self, obj, stream):
        Int64.pack(self.storer(obj), stream)
    def unpack(self, stream):
        return self.loader(Int64.unpack(stream))

class Date(Packer):
    __slots__ = []
    @classmethod
    def pack(cls, obj, stream):
        ts = time.mktime(obj.timetuple()) + (obj.microsecond/1000000.0)
        Int64.pack(int(ts * 1000), stream)
    @classmethod
    def unpack(cls, stream):
        ts = Int64.unpack(stream)
        return datetime.fromtimestamp(ts / 1000.0)

class Buffer(Packer):
    __slots__ = []
    @classmethod
    def pack(cls, obj, stream):
        if obj is None:
            obj = []
        Int32.pack(len(obj), stream)
        stream.write(obj)
    @classmethod
    def unpack(cls, stream):
        length = Int32.unpack(stream)
        return stream.read(length)

class Str(Packer):
    __slots__ = []
    @classmethod
    def pack(cls, obj, stream):
        if obj is None:
            obj = ""
        Buffer.pack(obj.encode("utf-8"), stream)
    @classmethod
    def unpack(cls, stream):
        return Buffer.unpack(stream).decode("utf-8")

class ListOf(Packer):
    __slots__ = ["type"]
    def __init__(self, type):
        self.type = type
    def pack(self, obj, stream):
        Int32.pack(len(obj), stream)
        for item in obj:
            self.type.pack(item, stream)
    def unpack(self, stream):
        length = Int32.unpack(stream)
        obj = []
        for i in xrange(length):
            obj.append(self.type.unpack(stream))
        return obj

class MapOf(Packer):
    __slots__ = ["keytype", "valtype"]
    def __init__(self, keytype, valtype):
        self.keytype = keytype
        self.valtype = valtype
    def pack(self, obj, stream):
        Int32.pack(len(obj), stream)
        for key, val in obj.iteritems():
            self.keytype.pack(key, stream)
            self.valtype.pack(val, stream)
    def unpack(self, stream):
        length = Int32.unpack(stream)
        obj = {}
        for i in xrange(length):
            k = self.keytype.unpack(stream)
            v = self.valtype.unpack(stream)
            obj[k] = v
        return obj

