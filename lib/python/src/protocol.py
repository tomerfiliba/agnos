import sys
import itertools
import traceback
import weakref
from subprocess import Popen, PIPE
from .packers import Int8, Int32, Int64, Str
from . import transports


CMD_PING = 0
CMD_INVOKE = 1
CMD_QUIT = 2
CMD_DECREF = 3
CMD_INCREF = 4

REPLY_SUCCESS = 0
REPLY_PROTOCOL_ERROR = 1
REPLY_PACKED_EXCEPTION = 2
REPLY_GENERIC_EXCEPTION = 3

AGNOS_MAGIC = 0x5af30cf7

class PackedException(Exception):
    def pack(self, stream):
        raise NotImplementedError()
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
    AGNOS_VERSION = None
    IDL_MAGIC = None
    
    def __init__(self):
        self.cells = {}
    
    def post_init(self, func_mapping, packed_exceptions, exception_map):
        self.func_mapping = func_mapping
        self.packed_exceptions = packed_exceptions
        self.exception_map = exception_map
    
    def handshake(self, instream, outstream):
        with outstream.transaction() as trans:
            packers.Int32.pack(trans, AGNOS_MAGIC)
            packers.Str.pack(trans, self.AGNOS_VERSION)
            packers.Str.pack(trans, self.IDL_MAGIC)
        magic = packers.Int32.unpack(trans)
        if magic != AGNOS_MAGIC:
            raise HandshakeError("wrong magic: %r" % (magic,))
        succ = packers.Int32.unpack(trans)
        if succ != 1:
            raise HandshakeError("client rejected connection")
    
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

    def send_protocol_error(self, stream, seq, exc):
        Int32.pack(seq, stream)
        Int8.pack(REPLY_PROTOCOL_ERROR, stream)
        Str.pack(str(exc), stream)
    
    def send_generic_exception(self, stream, seq, exc): 
        Int32.pack(seq, stream)
        Int8.pack(REPLY_GENERIC_EXCEPTION, stream)
        Str.pack(exc.msg, stream)
        Str.pack(exc.traceback, stream)

    def send_packed_exception(self, stream, seq, exc): 
        Int32.pack(seq, stream)
        Int8.pack(REPLY_PACKED_EXCEPTION, stream)
        Int32.pack(exc._recid, stream)
        packer = self.packed_exceptions[type(exc)]
        packer.pack(exc, stream)
    
    def process(self, instream, outstream):
        seq = Int32.unpack(instream)
        cmd = Int8.unpack(instream)
        
        with outstream.transaction() as trans:
            try:
                if cmd == CMD_INVOKE:
                    self.process_invoke(instream, trans, seq)
                elif cmd == CMD_PING:
                    self.process_ping(instream, trans, seq)
                elif cmd == CMD_DECREF:
                    self.process_decref(instream, trans, seq)
                elif cmd == CMD_QUIT:
                    self.process_quit(instream, trans, seq)
                else:
                    raise ProtocolError("unknown command code: %d" % (cmd,))
            except ProtocolError, ex:
                trans.clear()
                self.send_protocol_error(trans, seq, ex)
            except GenericException, ex:
                trans.clear()
                self.send_generic_exception(trans, seq, ex)
            except PackedException, ex:
                trans.clear()
                self.send_packed_exception(trans, seq, ex)

    def process_ping(self, instream, outstream, seq):
        msg = Str.unpack(instream)
        Int32.pack(seq, outstream)
        Int8.pack(REPLY_SUCCESS, outstream)
        Str.pack(msg, outstream)

    def process_decref(self, instream, outstream, seq):
        oid = Int64.unpack(instream)
        self.decref(oid)

    def process_incref(self, instream, outstream, seq):
        oid = Int64.unpack(instream)
        self.incref(oid)

    def process_quit(self, instream, outstream, seq):
        raise KeyboardInterrupt()

    def process_invoke(self, instream, outstream, seq):
        funcid = Int32.unpack(instream)
        try:
            func, unpack_args, res_packer = self.func_mapping[funcid]
        except KeyError:
            raise ProtocolError("unknown function id: %d" % (funcid,))
        args = unpack_args(instream)
        try:
            res = func(args)
        except PackedException, ex:
            raise
        except ProtocolError, ex:
            raise
        except Exception, ex:
            raise self.pack_exception(*sys.exc_info())
        else:
            Int32.pack(seq, outstream)
            Int8.pack(REPLY_SUCCESS, outstream)
            if res_packer:
                res_packer.pack(res, outstream)
    
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


class BaseClient(object):
    REPLY_SLOT_EMPTY = 1
    REPLY_SLOT_SUCCESS = 2
    REPLY_SLOT_ERROR = 3
    REPLY_SLOT_DISCARDED = 4
    PACKED_EXCEPTIONS = {}
    
    def __init__(self, instream, outstream):
        self._instream = instream
        self._outstream = outstream 
        self._seq = itertools.count()
        self._replies = {}
        self._proxy_cache = weakref.WeakValueDictionary()
        self._handshake()
    
    def __del__(self):
        self.close()
    
    def _handshake(self):
        raise NotImplementedError()
    
    def close(self):
        if self._instream:
            self._instream.close()
            self._outstream.close()
            self._instream = None
            self._outstream = None

    def _decref(self, oid):
        seq = self._seq.next()
        try:
            with self._outstream.transaction():
                Int32.pack(seq, self._outstream)
                Int8.pack(CMD_DECREF, self._outstream)
                Int64.pack(oid, self._outstream)
        except Exception:
            pass
    
    def _get_proxy(self, cls, objref):
        if objref in self._proxy_cache:
            return self._proxy_cache[objref]
        else:
            proxy = cls(self, objref)
            self._proxy_cache[objref] = proxy
            return proxy

    def _send_invocation(self, stream, funcid, reply_packer):
        seq = self._seq.next()
        Int32.pack(seq, stream)
        Int8.pack(CMD_INVOKE, stream)
        Int32.pack(funcid, stream)
        self._replies[seq] = (self.REPLY_SLOT_EMPTY, reply_packer)
        return seq

    def _load_packed_exception(self):
        clsid = Int32.unpack(self._instream)
        try:
            packer = self.PACKED_EXCEPTIONS[clsid]
        except KeyError:
            raise ProtocolError("invalid class id: %d" % (clsid,))
        return packer.unpack(self._instream)

    def _load_protocol_error(self):
        msg = Str.unpack(self._instream)
        return ProtocolError(msg)

    def _load_generic_exception(self):
        msg = Str.unpack(self._instream)
        tb = Str.unpack(self._instream)
        return GenericException(msg, tb)

    def _process_incoming(self, timeout):
        if not self._instream.poll(timeout):
            return
        seq = Int32.unpack(self._instream)
        code = Int8.unpack(self._instream)
        tp, packer = self._replies.get(seq, (None, None))
        if tp != self.REPLY_SLOT_EMPTY and tp != self.REPLY_SLOT_DISCARDED:
            raise ProtocolError("invalid sequence number %d" % (seq,))
        
        if code == REPLY_SUCCESS:
            if packer:
                val = packer.unpack(self._instream)
            else:
                val = None
            self._replies[seq] = (self.REPLY_SLOT_SUCCESS, val)
        elif code == REPLY_PACKED_EXCEPTION:
            self._replies[seq] = (self.REPLY_SLOT_ERROR, self._load_packed_exception())
        elif code == REPLY_GENERIC_EXCEPTION:
            self._replies[seq] = (self.REPLY_SLOT_ERROR, self._load_generic_exception())
        elif code == REPLY_PROTOCOL_ERROR:
            # protocol errors are not enqueued, because the stream has probably
            # been corrupted, so we stop as ealry as possible 
            raise self._load_protocol_error()
        else:
            raise ProtocolError("unknown reply code: %d" % (code,))
        
        if tp == self.REPLY_SLOT_DISCARDED:
            del self._replies[seq]
    
    def _reply_ready(self, seq):
        return self._replies[seq][0] != self.REPLY_SLOT_EMPTY
    
    def _wait_reply(self, seq, timeout = None):
        while not self._reply_ready(seq):
            self._process_incoming(timeout)
        return self._replies.pop(seq)
    
    def _get_reply(self, seq, timeout = None):
        type, obj = self._wait_reply(seq, timeout)
        if type == self.REPLY_SLOT_SUCCESS:
            return obj
        elif type == self.REPLY_SLOT_ERROR:
            raise obj
        else:
            raise ValueError("invalid reply slot type: %r" % (seq,))











