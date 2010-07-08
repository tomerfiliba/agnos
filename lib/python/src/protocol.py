import sys
import itertools
import traceback
import weakref
from subprocess import Popen, PIPE
from contextlib import contextmanager
from .packers import Int8, Int32, Int64, Str, BuiltinHeteroMapPacker
from . import transports


CMD_PING = 0
CMD_INVOKE = 1
CMD_QUIT = 2
CMD_DECREF = 3
CMD_INCREF = 4
CMD_GETINFO = 5

REPLY_SUCCESS = 0
REPLY_PROTOCOL_ERROR = 1
REPLY_PACKED_EXCEPTION = 2
REPLY_GENERIC_EXCEPTION = 3

INFO_META = 0
INFO_GENERAL = 1
INFO_FUNCTIONS = 2
INFO_FUNCCODES = 3

AGNOS_MAGIC = 0x5af30cf7


class PackedException(Exception):
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

class HandshakeError(ProtocolError):
    pass


class BaseProxy(object):
    __slots__ = ["_client", "_objref", "__weakref__"]
    def __init__(self, client, objref):
        self._client = weakref.proxy(client)
        self._objref = objref
    def __del__(self):
        self.dispose()
    def __repr__(self):
        if self._client is None:
            return "<%s instance (disposed)>" % (self.__class__.__name__,)
        else:
            return "<%s instance @ %s>" % (self.__class__.__name__, self._objref)

    def dispose(self):
        if self._client is None:
            return
        self._client._decref(self._objref)
        self._client = None
        self._objref = None


class BaseProcessor(object):
    def __init__(self):
        self.cells = {}
    
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

    def send_protocol_error(self, transport, exc):
        Int8.pack(REPLY_PROTOCOL_ERROR, transport)
        Str.pack(str(exc), transport)
    
    def send_generic_exception(self, transport, exc): 
        Int8.pack(REPLY_GENERIC_EXCEPTION, transport)
        Str.pack(exc.msg, transport)
        Str.pack(exc.traceback, transport)

    def send_packed_exception(self, transport, exc): 
        Int8.pack(REPLY_PACKED_EXCEPTION, transport)
        Int32.pack(exc._recid, transport)
        packer = self.packed_exceptions[type(exc)]
        packer.pack(exc, transport)
    
    def process(self, transport):
        with transport.reading() as seq:
            cmd = Int8.unpack(transport)
            with transport.writing(seq):
                try:
                    if cmd == CMD_INVOKE:
                        self.process_invoke(transport, seq)
                    elif cmd == CMD_PING:
                        self.process_ping(transport, seq)
                    elif cmd == CMD_DECREF:
                        self.process_decref(transport, seq)
                    elif cmd == CMD_QUIT:
                        self.process_quit(transport, seq)
                    elif cmd == CMD_GETINFO:
                        self.process_get_info(transport, seq)
                    else:
                        raise ProtocolError("unknown command code: %d" % (cmd,))
                except ProtocolError, ex:
                    transport.reset()
                    self.send_protocol_error(transport, ex)
                except GenericException, ex:
                    transport.reset()
                    self.send_generic_exception(transport, ex)
                except PackedException, ex:
                    transport.reset()
                    self.send_packed_exception(transport, ex)

    def process_ping(self, transport, seq):
        msg = Str.unpack(transport)
        Int8.pack(REPLY_SUCCESS, transport)
        Str.pack(msg, transport)

    def process_decref(self, transport, seq):
        oid = Int64.unpack(transport)
        self.decref(oid)

    def process_incref(self, transport, seq):
        oid = Int64.unpack(transport)
        self.incref(oid)

    def process_quit(self, transport, seq):
        raise KeyboardInterrupt()

    def process_get_info(self, transport, seq):
        code = Int32.unpack(transport)
        info = HeteroMap()
        
        if code == INFO_GENERAL:
            self.process_get_general_info(info)
        elif code == INFO_FUNCTIONS:
            self.process_get_functions_info(info)
        elif code == INFO_FUNCCODES:
            self.process_get_function_codes(info)
        else: # INFO_META:
            info["INFO_META"] = INFO_META
            info["INFO_GENERAL"] = INFO_GENERAL
            info["INFO_FUNCTIONS"] = INFO_FUNCTIONS
            info["INFO_FUNCCODES"] = INFO_FUNCTIONS
        
        Int8.pack(REPLY_SUCCESS, transport)
        BuiltinHeteroMapPacker.pack(info, transport)

    def process_invoke(self, transport, seq):
        funcid = Int32.unpack(transport)
        try:
            func, unpack_args, res_packer = self.func_mapping[funcid]
        except KeyError:
            raise ProtocolError("unknown function id: %d" % (funcid,))
        args = unpack_args(transport)
        try:
            res = func(args)
        except PackedException, ex:
            raise
        except ProtocolError, ex:
            raise
        except Exception, ex:
            raise self.pack_exception(*sys.exc_info())
        else:
            Int32.pack(seq, transport)
            Int8.pack(REPLY_SUCCESS, transport)
            if res_packer:
                res_packer.pack(res, transport)
    
    def pack_exception(self, typ, val, tb):
        if typ not in self.exception_map:
            tbtext = "".join(traceback.format_exception(typ, val, tb)[:-1])
            return GenericException(repr(val), tbtext)
        
        packed_type = self.exception_map[typ]
        attrs = {}
        for name in packed_type._ATTRS:
            if hasattr(val, name):
                attrs[name] = getattr(val, name)
        for v, name in zip(val, packed_type._ATTRS):
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


class BaseClientUtils(object):
    REPLY_SLOT_EMPTY = 1
    REPLY_SLOT_SUCCESS = 2
    REPLY_SLOT_ERROR = 3
    REPLY_SLOT_DISCARDED = 4
    
    def __init__(self, transport, packed_exceptions):
        self.transport = transport
        self.seq = itertools.count()
        self.replies = {}
        self.proxy_cache = weakref.WeakValueDictionary()
        self.packed_exceptions = packed_exceptions
    
    def __del__(self):
        self.close()
    
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
    
    def get_proxy(self, cls, objref):
        if objref < 0:
            return None
        if objref in self.proxy_cache:
            return self.proxy_cache[objref]
        else:
            proxy = cls(self, objref)
            self.proxy_cache[objref] = proxy
            return proxy

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
        replies[seq] = (self.REPLY_SLOT_EMPTY, Str)
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
        replies[seq] = (self.REPLY_SLOT_EMPTY, BuiltinHeteroMapPacker)
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











