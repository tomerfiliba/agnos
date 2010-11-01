##############################################################################
# Part of the Agnos RPC Framework
#    http://agnos.sourceforge.net
#
# Copyright 2010, Tomer Filiba (tomerf@il.ibm.com; tomerfiliba@gmail.com)
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

from datetime import datetime
import threading
try:
    long
except NameError:
    long = int
try:
    basestring
except NameError:
    basestring = str


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
    cls._idl_type = name
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
    
    def new_map(self, name):
        from . import packers
        map2 = HeteroMap()
        self.add(name, self._get_packer(name, None), map2, packers.BuiltinHeteroMapPacker)
        return map2
    
    def add(self, key, keypacker, val, valpacker):
        if keypacker is None:
            raise TypeError("keypacker not given")
        if valpacker is None:
            raise TypeError("valpacker not given")
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
    __iter__ = iterkeys
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
        keypacker = self._get_packer(key)
        valpacker = self._get_packer(val)
        if not keypacker:
            raise TypeError("cannot deduce packer for key %r" % (key,))
        if not valpacker:
            raise TypeError("cannot deduce packer for value %r" % (val,))
        self.add(key, keypacker, val, valpacker)
    def _get_packer(self, obj):
        from . import packers
        if obj is None:
            return packers.Null
        elif isinstance(obj, basestring):
            return packers.Str
        elif isinstance(obj, bool):
            return packers.Bool
        elif isinstance(obj, int):
            if obj < MAX_INT32:
                return packers.Int32
            else:
                return packers.Int64
        elif isinstance(obj, long):
            return packers.Int64
        elif isinstance(obj, float):
            return packers.Float
        elif isinstance(obj, datetime):
            return packers.Date
        elif isinstance(obj, bytes):
            return packers.Buffer
        else:
            return None
        




