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

import sys
import traceback
import weakref
import time
from . import utils
from subprocess import Popen, PIPE
from contextlib import contextmanager
from .packers import Int8, Int32, Int64, Str, Bool, BuiltinHeteroMapPacker 
from .packers import PackingError
from .compat import icount
from . import transports
from . import httptransport


CMD_PING = 0
CMD_INVOKE = 1
CMD_QUIT = 2
CMD_DECREF = 3
CMD_INCREF = 4
CMD_GETINFO = 5
CMD_CHECK_CAST = 6
CMD_QUERY_PROXY_TYPE = 7

REPLY_SUCCESS = 0
REPLY_PROTOCOL_ERROR = 1
REPLY_PACKED_EXCEPTION = 2
REPLY_GENERIC_EXCEPTION = 3

INFO_META = 0
INFO_SERVICE = 1
INFO_FUNCTIONS = 2
INFO_REFLECTION = 3


class BaseRecord(object):
    def __eq__(self, other):
        return type(other) == type(self) and self.__dict__ == other.__dict__
    def __ne__(self, other):
        return not (self == other)

class PackedException(Exception, BaseRecord):
    def __str__(self):
        return repr(self)
    # to override python (>= 2.6) stupid warnings
    def _get_message(self):
        return self._message
    def _set_message(self, val):
        self._message = val
    message = property(_get_message, _set_message)

class GenericException(Exception):
    def __init__(self, msg, traceback):
        self.msg = msg
        self.traceback = traceback
    def __str__(self):
        return "%s\n---------------- Remote Traceback ----------------\n%s" % (
            self.msg, self.traceback)

class ProtocolError(Exception):
    pass

class WrongAgnosVersion(ProtocolError):
    pass
class WrongServiceName(ProtocolError):
    pass
class IncompatibleServiceVersion(ProtocolError):
    pass


class BaseProxy(object):
    __slots__ = ["_client", "_objref", "_disposed", "__weakref__"]
    def __init__(self, client, objref, owns_ref):
        self._client = weakref.proxy(client)
        self._objref = objref
        self._disposed = not owns_ref
    def __del__(self):
        self.dispose()
    def __repr__(self):
        if self._disposed:
            return "<%s instance (disposed)>" % (self.__class__.__name__,)
        else:
            return "<%s instance @ %s>" % (self.__class__.__name__, self._objref)
    
    def __eq__(self, other):
        return isinstance(other, BaseProxy) and self._client == other._client \
            and self._objref == other._objref
    def __ne__(self, other):
        return not (self == other)

    def dispose(self):
        if self._disposed:
            return
        self._disposed = True
        self._client._utils.decref(self._objref)
        self._client = None
        self._objref = None
    
    def get_remote_type(self):
        return self._client._utils.get_proxy_type(self._objref)


class BaseProcessor(object):
    def __init__(self, transport):
        self.transport = transport
        self.cells = {}
    
    def close(self):
        self.transport.close()
    
    def fileno(self):
        return self.transport.fileno()
    
    def post_init(self, func_mapping, packed_exceptions, exception_map):
        self.func_mapping = func_mapping
        self.packed_exceptions = packed_exceptions
        self.exception_map = exception_map
    
    def store(self, obj):
        if obj is None:
            return -1
        oid = id(obj)
        if oid in self.cells:
            ref = self.cells[oid][0]
        else:
            ref = 0
        self.cells[oid] = (ref + 1, obj)
        return oid
    
    def load(self, oid):
        if oid < 0:
            return None
        return self.cells[oid][1]
    
    def decref(self, oid):
        if oid not in self.cells:
            return
        ref, obj = self.cells[oid]
        if ref <= 1:
            del self.cells[oid]
        else:
            self.cells[oid] = (ref - 1, obj)

    def incref(self, oid):
        if oid not in self.cells:
            return
        ref, obj = self.cells[oid]
        self.cells[oid] = (ref + 1, obj)

    def send_protocol_error(self, exc):
        Int8.pack(REPLY_PROTOCOL_ERROR, self.transport)
        Str.pack(str(exc), self.transport)
    
    def send_generic_exception(self, exc): 
        Int8.pack(REPLY_GENERIC_EXCEPTION, self.transport)
        Str.pack(exc.msg, self.transport)
        Str.pack(exc.traceback, self.transport)

    def send_packed_exception(self, exc): 
        Int8.pack(REPLY_PACKED_EXCEPTION, self.transport)
        Int32.pack(exc._idl_id, self.transport)
        packer = self.packed_exceptions[type(exc)]
        packer.pack(exc, self.transport)
    
    def process(self):
        with self.transport.reading() as seq:
            cmd = Int8.unpack(self.transport)
            with self.transport.writing(seq):
                try:
                    if cmd == CMD_INVOKE:
                        self.process_invoke(seq)
                    elif cmd == CMD_PING:
                        self.process_ping(seq)
                    elif cmd == CMD_DECREF:
                        self.process_decref(seq)
                    elif cmd == CMD_QUIT:
                        self.process_quit(seq)
                    elif cmd == CMD_GETINFO:
                        self.process_get_info(seq)
                    elif cmd == CMD_QUERY_PROXY_TYPE:
                        self.process_query_proxy_type(seq)
                    elif cmd == CMD_CHECK_CAST:
                        self.process_check_cast(seq)
                    else:
                        raise ProtocolError("unknown command code: %d" % (cmd,))
                except ProtocolError as ex:
                    self.transport.restart_write()
                    self.send_protocol_error(ex)
                except GenericException as ex:
                    self.transport.restart_write()
                    self.send_generic_exception(ex)
                except PackingError as ex:
                    tbtext = "".join(traceback.format_exception(*sys.exc_info())[:-1])
                    self.transport.restart_write()
                    self.send_generic_exception(GenericException(str(ex), tbtext))
                except PackedException as ex:
                    self.transport.restart_write()
                    self.send_packed_exception(ex)

    def process_ping(self, seq):
        msg = Str.unpack(self.transport)
        Int8.pack(REPLY_SUCCESS, self.transport)
        Str.pack(msg, self.transport)

    def process_decref(self, seq):
        oid = Int64.unpack(self.transport)
        self.decref(oid)
    
    def process_query_proxy_type(self, seq):
        oid = Int64.unpack(self.transport)
        tp = type(self.load(oid))
        Int8.pack(REPLY_SUCCESS, self.transport)
        #Str.pack(tp._idl_type, self.transport)
        Str.pack(tp.__module__ + "." + tp.__name__, self.transport)

    def process_check_cast(self, seq):
        oid = Int64.unpack(self.transport)
        idl_class_name = Str.unpack(self.transport)
        tp = type(self.load(oid))
        res = _idl in tp._idl_super_classes
        Int8.pack(REPLY_SUCCESS, self.transport)
        Bool.pack(res, self.transport)

    def process_incref(self, seq):
        oid = Int64.unpack(self.transport)
        self.incref(oid)

    def process_quit(self, seq):
        raise KeyboardInterrupt()

    def process_get_info(self, seq):
        code = Int32.unpack(self.transport)
        info = utils.HeteroMap()
        
        if code == INFO_SERVICE:
            self.process_get_service_info(info)
        elif code == INFO_FUNCTIONS:
            self.process_get_functions_info(info)
        elif code == INFO_REFLECTION:
            self.process_get_reflection_info(info)
        else: # INFO_META
            self.process_get_meta_info(info)
        
        Int8.pack(REPLY_SUCCESS, self.transport)
        BuiltinHeteroMapPacker.pack(info, self.transport)

    def process_invoke(self, seq):
        funcid = Int32.unpack(self.transport)
        try:
            func, unpack_args, res_packer = self.func_mapping[funcid]
        except KeyError:
            raise ProtocolError("unknown function id: %d" % (funcid,))
        args = unpack_args()
        try:
            res = func(args)
        except PackedException:
            raise
        except ProtocolError:
            raise
        except Exception:
            raise self.pack_exception(*sys.exc_info())
        else:
            Int8.pack(REPLY_SUCCESS, self.transport)
            if res_packer:
                res_packer.pack(res, self.transport)
    
    def pack_exception(self, typ, val, tb):
        if typ not in self.exception_map:
            tbtext = "".join(traceback.format_exception(typ, val, tb)[:-1])
            return GenericException(repr(val), tbtext)
        
        packed_type = self.exception_map[typ]
        attrs = {}
        for name in packed_type._idl_attrs:
            if hasattr(val, name):
                attrs[name] = getattr(val, name)
        for v, name in zip(val, packed_type._idl_attrs):
            if name not in attrs:
                attrs[name] = v
        ex2 = packed_type(**attrs)
        return ex2


class Namespace(object):
    def __setitem__(self, name, obj):
        parts = name.split(".")
        ns = self
        for part in parts[:-1]:
            if not hasattr(ns, part):
                setattr(ns, part, Namespace())
            ns = getattr(ns, part)
            if not isinstance(ns, Namespace):
                raise TypeError("%r is not a namespace" % (name,))
        setattr(ns, parts[-1], obj)


class ClientUtils(object):
    REPLY_SLOT_EMPTY = 1
    REPLY_SLOT_SUCCESS = 2
    REPLY_SLOT_ERROR = 3
    REPLY_SLOT_DISCARDED = 4
    
    def __init__(self, transport, packed_exceptions):
        self.transport = transport
        self.seq = icount()
        self.replies = {}
        self.proxy_cache = weakref.WeakValueDictionary()
        self.packed_exceptions = packed_exceptions
    
    def __del__(self):
        try:
            self.close()
        except Exception:
            pass
    
    def close(self):
        self.transport.close()

    def decref(self, oid):
        seq = self.seq.next()
        try:
            with self.transport.writing(seq):
                Int8.pack(CMD_DECREF, transport)
                Int64.pack(oid, transport)
        except Exception:
            pass
    
    def get_proxy(self, cls, owner, objref):
        if objref < 0:
            return None
        if objref in self.proxy_cache:
            return self.proxy_cache[objref]
        else:
            proxy = cls(owner, objref, True)
            self.proxy_cache[objref] = proxy
            return proxy

    def check_cast(self, objref, clsname):
        seq = self.seq.next()
        with self.transport.writing(seq):
            Int8.pack(CMD_CHECK_CAST, self.transport)
            Int64.pack(objref, self.transport)
            Str.pack(clsname, self.transport)
        self.replies[seq] = (self.REPLY_SLOT_EMPTY, Bool)
        return self.get_reply(seq)

    def get_proxy_type(self, objref):
        seq = self.seq.next()
        with self.transport.writing(seq):
            Int8.pack(CMD_QUERY_PROXY_TYPE, self.transport)
            Int64.pack(objref, self.transport)
        self.replies[seq] = (self.REPLY_SLOT_EMPTY, Str)
        return self.get_reply(seq)

    @contextmanager
    def invocation(self, funcid, reply_packer):
        seq = self.seq.next()
        with self.transport.writing(seq):
            Int8.pack(CMD_INVOKE, self.transport)
            Int32.pack(funcid, self.transport)
            self.replies[seq] = (self.REPLY_SLOT_EMPTY, reply_packer)
            yield seq
    
    def tunnel_request(self, blob):
        seq = self.seq.next()
        with self.transport.writing(seq):
            self.transport.write(blob)
        self.replies[seq] = (self.REPLY_SLOT_EMPTY, NotImplemented)
        return seq
    
    def load_packed_exception(self):
        clsid = Int32.unpack(self.transport)
        try:
            packer = self.packed_exceptions[clsid]
        except KeyError:
            raise ProtocolError("invalid class id: %d" % (clsid,))
        return packer.unpack(self.transport)

    def load_protocol_error(self):
        msg = Str.unpack(self.transport)
        return ProtocolError(msg)

    def load_generic_exception(self):
        msg = Str.unpack(self.transport)
        tb = Str.unpack(self.transport)
        return GenericException(msg, tb)
    
    def ping(self, payload, timeout):
        seq = self.seq.next()
        with self.transport.writing(seq):
            Int8.pack(CMD_PING, self.transport)
            Str.pack(payload, self.transport)
        self.replies[seq] = (self.REPLY_SLOT_EMPTY, Str)
        t0 = time.time()
        payload2 = self.get_reply(seq, timeout)
        dt = time.time() - t0
        if payload2 != payload:
            raise ProtocolError("ping reply does not match payload")
        return dt
    
    def get_service_info(self, code):
        seq = self.seq.next()
        with self.transport.writing(seq):
            Int8.pack(CMD_GETINFO, self.transport)
            Int32.pack(code, self.transport)
        self.replies[seq] = (self.REPLY_SLOT_EMPTY, BuiltinHeteroMapPacker)
        return self.get_reply(seq)

    def process_incoming(self, timeout):
        with self.transport.reading(timeout) as seq:
            code = Int8.unpack(self.transport)
            tp, packer = self.replies.get(seq, (None, None))
            if tp != self.REPLY_SLOT_EMPTY and tp != self.REPLY_SLOT_DISCARDED:
                raise ProtocolError("invalid sequence number %d" % (seq,))
            if code == REPLY_SUCCESS:
                if packer is NotImplemented:
                    val = self.transport.read_all()
                elif packer:
                    val = packer.unpack(self.transport)
                else:
                    val = None
                self.replies[seq] = (self.REPLY_SLOT_SUCCESS, val)
            elif code == REPLY_PACKED_EXCEPTION:
                self.replies[seq] = (self.REPLY_SLOT_ERROR, self.load_packed_exception())
            elif code == REPLY_GENERIC_EXCEPTION:
                self.replies[seq] = (self.REPLY_SLOT_ERROR, self.load_generic_exception())
            elif code == REPLY_PROTOCOL_ERROR:
                # protocol errors are not enqueued, because the stream has probably
                # been corrupted, so we stop as ealry as possible 
                raise self.load_protocol_error()
            else:
                raise ProtocolError("unknown reply code: %d" % (code,))
            
            if tp == self.REPLY_SLOT_DISCARDED:
                del self.replies[seq]
    
    def is_reply_ready(self, seq):
        tp = self.replies[seq][0]
        return tp != self.REPLY_SLOT_EMPTY and tp != self.REPLY_SLOT_DISCARDED
    
    def discard_reply(self, seq):
        if seq in self.replies:
            if self.is_reply_ready(seq):
                del self.replies[seq]
            else:
                tp, val = self.replies[seq]
                self.replies[seq] = (self.REPLY_SLOT_DISCARDED, val)
    
    def wait_reply(self, seq, timeout = None):
        if timeout is not None:
            tend = time.time() + timeout
        else:
            remaining = None
        while not self.is_reply_ready(seq):
            if timeout is not None:
                remaining = tend - time.time() 
            self.process_incoming(remaining)
        return self.replies.pop(seq)
    
    def get_reply(self, seq, timeout = None):
        type, obj = self.wait_reply(seq, timeout)
        if type == self.REPLY_SLOT_SUCCESS:
            return obj
        elif type == self.REPLY_SLOT_ERROR:
            raise obj
        else:
            raise ValueError("invalid reply slot type: %r" % (seq,))


class BaseClient(object):
    def __enter__(self):
        pass
    def __exit__(self, *args):
        self.close()
    
    @classmethod
    def connect(cls, host, port, checked = True):
        return cls(transports.SocketTransport.connect(host, port), checked)
    @classmethod
    def connect_executable(cls, filename, args = None, checked = True):
        if args is None:
            return cls(transports.ProcTransport.from_executable(filename), checked)
        else:
            return cls(transports.ProcTransport.from_executable(filename, args), checked)
    @classmethod
    def connect_proc(cls, proc, checked = True):
        return cls(transports.ProcTransport.from_proc(proc), checked)
    @classmethod
    def connect_url(cls, url, checked = True):
        return cls(httptransport.HttpClientTransport(url), checked)
    
    def close(self):
        self._utils.close()
    def get_service_info(self, code):
        return self._utils.get_service_info(code)
    def tunnel_request(self, blob):
        return self._utils.tunnel_request(code)





