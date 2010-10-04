from datetime import datetime
import packers
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
        return self._owner == threading.current_thread()


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

MAX_INT32 = 2 ** 31

class HeteroMap(object):
    def __init__(self, fields = None):
        if fields is None:
            self.fields = {}
        else:
            self.fields = fields
    
    def __repr__(self):
        text = "HeteroMap:\n" + "\n".join("%r = %r" % (k, v) for k, v in self.iteritems())
        return text.replace("\n", "\n  ")
    
    def add(self, key, keypacker, val, valpacker):
        self.fields[key] = (val, keypacker, valpacker)
        return val
    def clear(self):
        self.fields.clear()
    def copy(self):
        return HeteroMap(self.fields.copy())
    def get(self, default = None):
        return self.fields.get(key, (default,))[0]
    def items(self):
        return list(self.iteritems())
    def iteritems(self):
        for k, v in self.fields.iteritems():
            yield k, v[0]
    def iterkeys(self):
        return self.fields.iterkeys()
    def itervalues(self):
        for v in self.fields.itervalues():
            yield v[0]
    def iterfields(self):
        for k, v in self.fields.iteritems():
            vv, kp, vp = v
            yield k, kp, vv, vp
    def keys(self):
        return self.fields.keys()
    def pop(self, key, *default):
        if not default:
            return self.fields.pop(key)[0]
        elif len(default) == 1:
            return self.fields.pop(key, (default[0],))[0]
        else:
            raise TypeError("pop takes at most two arguments")
    def update(self, other):
        if isinstance(other, HeteroMap):
            self.fields.update(other.fields)
        else:
            for k, v in other.items():
                self[k] = v
    def values(self):
        return list(self.itervalues())
    def __len__(self):
        return len(self.fields)
    def __contains__(self, key):
        return key in self.fields
    has_key = __contains__
    def __getitem__(self, key):
        return self.fields[key][0]
    def __delitem__(self, key):
        del self.fields[key]
    def __setitem__(self, key, val):
        if key in self.fields:
            _, kp, vp = self.fields[key]
        else:
            kp = vp = None
        keypacker = self._get_packer(key, kp)
        valpacker = self._get_packer(val, vp)
        if not keypacker:
            raise TypeError("cannot deduce packer for %r" % (key,))
        if not valpacker:
            raise TypeError("cannot deduce packer for %r" % (val,))
        self.add(key, keypacker, val, valpacker)
    def _get_packer(self, obj, default):
        if isinstance(obj, basestring):
            return packers.Str
        if isinstance(obj, int) and obj < MAX_INT32:
            return packers.Int32
        if isinstance(obj, long):
            return packers.Int64
        if isinstance(obj, float):
            return packers.Float
        if isinstance(obj, datetime):
            return packers.Date
        if isinstance(obj, bytes):
            return packers.Buffer
        




