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

from datetime import datetime
import threading
import sys
import os
import time
import traceback
try:
    long
except NameError:
    long = int
try:
    basestring
except NameError:
    basestring = str
try:
    from zlib import decompressobj
except ImportError:
    def decompressobj():
        raise ImportError("zlib is not supported")


class RLock(object):
    """
    a version of threading.RLock that supports is_held_by_current_thread
    """
    
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
    """
    an implementation of an enum for python. use create_enum
    """
    
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
    """creates an enum class with the given name and given members"""
    cls = type(name, (Enum,), dict(_BY_VALUE = {}))
    cls._idl_type = name
    for n, v in members.items():
        em = cls(n, v)
        setattr(cls, n, em)
        cls._BY_VALUE[v] = em
    return cls

MAX_INT32 = 2 ** 31

class HeteroMap(object):
    """
    a heterogeneous map. basically same as a dict, but it also associates
    with each entry a packer for the key and a packer for the value, allowing 
    them to be serailized over the wire.
    
    when adding items using the [] operator (__setitem__), the HeteroMap 
    attempts to infer the packers for the given key and value. if this fails, 
    an exception is raised, and you will have to use the explicit add() method 
    """
    
    def __init__(self, _fields = None, **_kwargs):
        if _fields is None:
            self.fields = {}
        else:
            self.fields = _fields
        self.update(_kwargs)
    
    def __eq__(self, other):
        return isinstance(other, HeteroMap) and self.fields == other.fields
    def __ne__(self, other):
        return not (self == other)
    
    def __repr__(self):
        text = "HeteroMap:\n" + "\n".join("%r = %r" % (k, v) for k, v in self.iteritems())
        return text.replace("\n", "\n  ")
    
    def new_map(self, name):
        """creates a new HeteroMap, inserts it under the given key, and returns 
        it. it's a utility method used by the generated binding code, and is not
        expected to be useful for end users"""
        from . import packers
        map2 = HeteroMap()
        self.add(name, self._get_packer(name), map2, packers.BuiltinHeteroMapPacker)
        return map2
    
    def add(self, key, keypacker, val, valpacker):
        """adds the given key-value pair (with the given key and value packer)
        to the map. if the key already exists, it will be replaced"""
        if keypacker is None:
            raise TypeError("keypacker not given")
        if valpacker is None:
            raise TypeError("valpacker not given")
        self.fields[key] = (val, keypacker, valpacker)
        return val
    def clear(self):
        self.fields.clear()
    def copy(self):
        """returns a copy of this map"""
        return HeteroMap(self.fields.copy())
    def get(self, key, default = None):
        return self.fields.get(key, (default,))[0]
    def items(self):
        return list(self.iteritems())
    def iteritems(self):
        return ((k, v[0]) for k, v in self.fields.items())
    def iterkeys(self):
        return (k for k in self.fields.keys())
    __iter__ = iterkeys
    def itervalues(self):
        return (v[0] for v in self.fields.values())
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
    def popitem(self):
        k, (vv, kp, vp) = self.fields.popitem()
        return vv
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

class LogSink(object):
    def __init__(self, files):
        self.files = list(files)
        self.lock = threading.RLock()

    def add_file(self, dev):
        self.files.append(dev)

    def close(self):
        with self.lock:
            for f in self.files:
                f.close()
            del self.files[:]
    
    def write(self, line):
        with self.lock:
            pruned = []
            line = line + "\n"
            for f in self.files:
                try:
                    f.write(line)
                    f.flush()
                except IOError as ex:
                    pruned.append(f)
            for f in pruned:
                self.files.remove(f)

NullSink = LogSink([])
StdoutSink = LogSink([sys.stdout])
StderrSink = LogSink([sys.stderr])

class Logger(object):
    """lightweight, simple to use logger object"""
    
    DATE_FORMAT = "%y-%m-%d"
    TIME_FORMAT = "%H:%M:%S"
    LINE_FORMAT = "[{time}|{level:<10}|{source:<15}] {text}"
    
    def __init__(self, sink, name = None):
        self.sink = sink
        self.name = name
    
    def _log(self, level, text):
        line = self.LINE_FORMAT.format(
            level = level, 
            source = self.name, 
            text = text, 
            pid = os.getpid(), 
            tid = threading.current_thread().ident,
            time = time.strftime(self.TIME_FORMAT), 
            date = time.strftime(self.DATE_FORMAT),
        )
        self.sink.write(line)

    def sublogger(self, name):
        return Logger(self.sink, self.name + "." + name if self.name else name)
    
    @staticmethod
    def _autoformat(fmt, args):
        if args:
            fmt %= args
        return fmt
    
    def info(self, msg, *args):
        self._log("INFO", self._autoformat(msg, args))
    def warn(self, msg, *args):
        self._log("WARNING", self._autoformat(msg, args))
    def error(self, msg, *args):
        self._log("ERROR", self._autoformat(msg, args))
    def exception(self):
        tbtext = "".join(traceback.format_exception(*sys.exc_info())[:-1])
        self._log("EXCEPTION", tbtext)

NullLogger = Logger(NullSink)
StdoutLogger = Logger(StdoutSink)
StderrLogger = Logger(StderrSink)


class BoundedStream(object):
    """a fixed-length input stream (file-like object)"""
    
    def __init__(self, stream, length, skip_underlying, close_underlying):
        """
        if skip_underlying is True, all the unread data in the underlying 
        stream will be skipped when this stream is closed. 
        if close_underlying is True, the underlying stream will be closed
        when this stream is closed.
        """ 
        self.stream = stream
        self.remaining_length = length
        self.skip_underlying = skip_underlying
        self.close_underlying = close_underlying
    
    def available(self):
        """returns the number of remaining, unread bytes""" 
        return self.remaining_length
    
    def close(self):
        if self.stream is None:
            return
        if self.skip_underlying:
            self.skip(-1)
        if self.close_underlying:
            self.stream.close()
        self.stream = None
    
    def read(self, count = -1):
        """reads up to `count` bytes from the underlying stream. if the end
        of the stream is reached, less bytes will be read. on EOF, returns the
        empty string. if count is negative, reads all the available data"""
        if self.remaining_length <= 0:
            return ""
        if count < 0 or count > self.remaining_length:
            count = self.remaining_length
        data = self.stream.read(count)
        self.remaining_length -= len(data)
        return data
    
    def skip(self, count):
        """same as read(), only it does not return the buffer.
        if count < 0, skips all the unread data"""
        self.read(count)


class ZlibStream(object):
    """
    a version of encodings.zlib_codec.StreamReader that actually works
    """
    
    def __init__(self, stream, underlying_read_size = 1024):
        self.stream = stream
        self.underlying_read_size = underlying_read_size
        self.buffer = ""
        self.decompressobj = decompressobj()
    
    def close(self):
        self.stream.close()
    
    def read(self, count):
        if self.decompressobj is None:
            return ""
        while len(self.buffer) < count:
            chunk = self.stream.read(self.underlying_read_size)
            if not chunk:
                self.buffer += self.decompressobj.flush()
                self.decompressobj = None
                break
            self.buffer += self.decompressobj.decompress(chunk)
        data = self.buffer[:count]
        self.buffer = self.buffer[:count]
        return data




























