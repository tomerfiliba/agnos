from packers import Int32

class Enum(object):
    def __init__(self, name, value):
        self.name = name
        self.value = value
    def __repr__(self):
        return "%s(%r, %r)" % (self.name, self.member)
    def __eq__(self, other):
        if isinstance(other, Enum):
            return self.value == other.value
        else:
            return self.value == other
    def __ne__(self, other):
        return not (self == other)
    @classmethod
    def get_by_value(cls, val):
        return cls._BY_VALUE[val]
    @classmethod
    def pack(cls, obj, stream):
        Int32.pack(obj.value, stream)
    @classmethod
    def unpack(cls, stream):
        return cls.get_by_value(Int32.unpack(stream))

def create_enum(_name, **members):
    cls = type(_name, (Enum,), dict(_BY_VALUE = {}))
    for n, v in members.iteritems():
        em = cls(n, v)
        setattr(cls, n, em)
        cls._BY_VALUE[v] = em
    return cls

class BaseProxy(object):
    __slots__ = ["_client", "_objref", "_disposed"]
    def __init__(self, client, objref):
        self._client = client
        self._objref = objref
        self._disposed = False
    def __del__(self):
        self.dispose()
    def dispose(self):
        if self._disposed:
            return
        self._client._decref(self._objref)
        self._disposed = True





