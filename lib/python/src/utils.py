from packers import Int32
import threading


class RLock(object):
    def __init__(self):
        self._lock = threading.RLock()
        self._owner = None
        self._count = 0
    def acquire(self):
        assert self._count >= 0
        self._lock.acquire()
        self._owner = threading.current_thread()
        self._count += 1
    def release(self):
        assert self._count >= 0
        if self._count == 0:
            raise threading.ThreadError("released too many times")
        else:
            self._count -= 1
            if self._count == 0:
                self._owner = None
        self._lock.release()
    def is_held_by_current_thread(self):
        return self._owner == thread.current_thread()


class EnumError(Exception):
    pass

class Enum(object):
    def __init__(self, name, value):
        self.name = name
        self.value = value
    def __repr__(self):
        return "%s(%r = %r)" % (self.__class__.__name__, self.name, self.value)
    def __eq__(self, other):
        if isinstance(other, Enum):
            return self.value == other.value
        else:
            return self.value == other
    def __ne__(self, other):
        return not (self == other)
    @classmethod
    def get_by_value(cls, val):
        try:
            return cls._BY_VALUE[val]
        except KeyError:
            raise EnumError("no member with value %r" % (val,))
    @classmethod
    def get_by_name(cls, name):
        try:
            return getattr(cls, name)
        except AttrributeError:
            raise EnumError("no member named %r" % (val,))
    @classmethod
    def pack(cls, obj, stream):
        if not isinstance(obj, Enum):
            obj = cls.get_by_value(obj)
        Int32.pack(obj.value, stream)
    @classmethod
    def unpack(cls, stream):
        return cls.get_by_value(Int32.unpack(stream))

def create_enum(name, members):
    cls = type(name, (Enum,), dict(_BY_VALUE = {}))
    for n, v in members.iteritems():
        em = cls(n, v)
        setattr(cls, n, em)
        cls._BY_VALUE[v] = em
    return cls

def make_method(cls):
    def deco(func):
        setattr(cls, func.__name__, func)
    return deco





