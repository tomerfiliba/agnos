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

REPLY_SUCCESS = 0
REPLY_PROTOCOL_ERROR = 1
REPLY_PACKED_EXCEPTION = 2
REPLY_GENERIC_EXCEPTION = 3

class PackedException(Exception):
    def pack(self, stream):
        raise NotImplementedError()
    def __str__(self):
        return repr(self)
    # to overcome python's stupid warnings
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
        return "\n---------------- Remote Traceback ----------------\n" + self.traceback

class ProtocolError(Exception):
    pass

class ChildServerError(Exception):
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
#    def __eq__(self, other):
#        if not isinstance(other, BaseProxy):
#            return NotImplemented
#        else:
#            return self._client == other._client and self._objref == other._objref
#    def __ne__(self, other):
#        return not (self == other)

    def dispose(self):
        if self._client is None:
            return
        self._client._decref(self._objref)
        self._client = None
        self._objref = None


class BaseProcessor(object):
    def __init__(self, func_mapping, exception_map):
        self.cells = {}
        self.exception_map = exception_map
        self.func_mapping = func_mapping
    
    def store(self, obj):
        oid = id(obj)
        if oid in self.cells:
            ref = self.cells[oid][0]
        else:
            ref = 0
        self.cells[oid] = (ref + 1, obj)
        return oid
    def load(self, oid):
        return self.cells[oid][1]
    def decref(self, oid):
        if oid not in self.cells:
            return
        ref, obj = self.cells[oid]
        if ref <= 1:
            del self.cells[oid]
        else:
            self.cells[oid] = (ref - 1, obj)
    
    def send_packed_exception(self, outstream, seq, exc):
        Int32.pack(seq, outstream)
        Int8.pack(REPLY_PACKED_EXCEPTION, outstream)
        exc.pack(outstream)
    
    def send_generic_exception(self, outstream, seq, exc):
        Int32.pack(seq, outstream)
        Int8.pack(REPLY_GENERIC_EXCEPTION, outstream)
        Str.pack(exc.msg, outstream)
        Str.pack(exc.traceback, outstream)
    
    def send_protocol_error(self, outstream, seq, exc):
        Int32.pack(seq, outstream)
        Int8.pack(REPLY_PROTOCOL_ERROR, outstream)
        Str.pack(tb, outstream)
    
    def process(self, instream, outstream):
        seq = Int32.unpack(instream)
        cmd = Int8.unpack(instream)
        with outstream.transaction():
            try:
                if cmd == CMD_INVOKE:
                    self.process_invoke(seq, instream, outstream)
                elif cmd == CMD_PING:
                    self.process_ping(seq, instream, outstream)
                elif cmd == CMD_DECREF:
                    self.process_decref(seq, instream, outstream)
                elif cmd == CMD_QUIT:
                    self.process_quit(seq, instream, outstream)
                else:
                    raise ProtocolError("unknown command code: %d" % (cmd,))
            except ProtocolError, ex:
                self.send_protocol_error(outstream, seq, ex)
            except PackedException, ex:
                self.send_packed_exception(outstream, seq, ex)
            except GenericException, ex:
                self.send_generic_exception(outstream, seq, ex)

    def process_ping(self, seq, instream, outstream):
        msg = Str.unpack(instream)
        Int32.pack(seq, outstream)
        Int8.pack(REPLY_SUCCESS, outstream)
        Str.pack(msg, outstream)

    def process_decref(self, seq, instream, outstream):
        oid = Int64.unpack(instream)
        self.decref(oid)

    def process_quit(self, seq, instream, outstream):
        raise KeyboardInterrupt()

    def process_invoke(self, seq, instream, outstream):
        funcid = Int32.unpack(instream)
        try:
            func, unpack_args, pack_res = self.func_mapping[funcid]
        except KeyError:
            raise ProtocolError("unknown function id: %d" % (funcid,))
        args = unpack_args(instream)
        try:
            res = func(args)
        except PackedException, ex:
            raise
        except Exception, ex:
            if type(ex) in self.exception_map:
                packed = self.exception_map[type(ex)]
                raise packed()
            else:
                tb = "".join(traceback.format_exception(*sys.exc_info()))
                raise GenericException(repr(ex), tb)
        Int32.pack(seq, outstream)
        Int8.pack(REPLY_SUCCESS, outstream)
        if pack_res:
            pack_res(res, outstream)


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
    REPLY_SLOT_EMPTY = 0
    REPLY_SLOT_SUCCESS = 1
    REPLY_SLOT_ERROR = 2
    PACKED_EXCEPTIONS = {}
    
    def __init__(self, instream, outstream):
        self._instream = instream
        self._outstream = outstream 
        self._seq = itertools.count()
        self._replies = {}
        self._proxy_cache = weakref.WeakValueDictionary()
    
    def __del__(self):
        self.close()
    
    @classmethod
    def from_transport(cls, transport):
        return cls(transport.get_input_stream(), transport.get_output_stream())
    
    @classmethod
    def connect(cls, host, port):
        return cls.from_transport(transports.SocketTransport.connect(host, port))
    
    @classmethod
    def connect_subproc(cls, proc):
        if not hasattr(proc, "stdout"):
            proc = Popen([proc, "-m", "child"], stdin = PIPE, stdout = PIPE) #, stderr = PIPE)
        hostname = proc.stdout.readline().strip()
        port = int(proc.stdout.readline().strip())
        proc.stdout.close()
        return cls.connect(hostname, port)
    
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

    def _invoke_command(self, funcid, reply_packer):
        seq = self._seq.next()
        Int32.pack(seq, self._outstream)
        Int8.pack(CMD_INVOKE, self._outstream)
        Int32.pack(funcid, self._outstream)
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
        if tp != self.REPLY_SLOT_EMPTY:
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
            raise ProtocolError("unknown reply code: %d" % (code,));
    
    def _reply_ready(self, seq):
        return self._replies[seq][0] != self.REPLY_SLOT_EMPTY
    
    def _wait_reply(self, seq, timeout = None):
        while not self._reply_ready(seq):
            self._process_incoming(timeout)
        return self._replies.pop(seq)
    
    def _get_reply(self, seq):
        type, obj = self._wait_reply(seq)
        if type == self.REPLY_SLOT_SUCCESS:
            return obj
        elif type == self.REPLY_SLOT_ERROR:
            raise obj
        else:
            raise ValueError("invalid reply slot type: %r" % (seq,))











