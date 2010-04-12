from .packers import Int8, Int32, Int64, Str
import itertools
from . import transports


CMD_PING = 0
CMD_INVOKE = 1
CMD_QUIT = 2
CMD_DECREF = 3

REPLY_SUCCESS = 0
REPLY_PROTOCOL_ERROR = 1
REPLY_PACKED_ERROR = 2
REPLY_GENERIC_ERROR = 3

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

class GenericError(Exception):
    pass

class ProtocolError(Exception):
    pass


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
        self._disposed = True
        self._client._decref(self._objref)


class BaseProcessor(object):
    def __init__(self, func_mapping):
        self.cells = {}
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
        ref = self.cells[oid][0]
        if ref <= 1:
            del self.cells[oid]
        else:
            self.cells[oid] = (ref - 1, obj)
    
    def send_packed_exception(self, outstream, seq, exc):
        with outstream.transaction():
            Int32.pack(seq, outstream)
            Int8.pack(REPLY_PACKED_ERROR, outstream)
            exc.pack(outstream)
    
    def send_generic_error(self, outstream, seq, exc):
        with outstream.transaction():
            Int32.pack(seq, outstream)
            Int8.pack(REPLY_GENERIC_ERROR, outstream)
            Str.pack(repr(exc), outstream)
    
    def send_protocol_error(self, outstream, seq, exc):
        with outstream.transaction():
            Int32.pack(seq, outstream)
            Int8.pack(REPLY_PROTOCOL_ERROR, outstream)
            Str.pack(repr(exc), outstream)
    
    def process(self, instream, outstream):
        seq = Int32.unpack(instream)
        cmd = Int8.unpack(instream)
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
        except Exception, ex:
            self.send_generic_error(outstream, seq, ex)

    def process_ping(self, seq, instream, outstream):
        with outstream.transaction():
            msg = Str.unpack(instream)
            Int32.pack(seq, outstream)
            Int8.pack(REPLY_SUCCESS, outstream)
            Str.pack(msg, outstream)

    def process_decref(self, seq, instream, outstream):
        with outstream.transaction():
            oid = Int64.unpack(instream)
            self.decref(oid)

    def process_quit(self, seq, instream, outstream):
        with outstream.transaction():
            pass

    def process_invoke(self, seq, instream, outstream):
        with outstream.transaction():
            funcid = Int32.unpack(instream)
            try:
                func, unpack_args, pack_res = self.func_mapping[funcid]
            except KeyError:
                raise ProtocolError("unknown function id: %d" % (funcid,))
            args = unpack_args(instream)
            res = func(args)
            Int32.pack(seq, outstream)
            Int8.pack(REPLY_SUCCESS, outstream)
            if pack_res:
                pack_res(res, outstream)


class BaseClient(object):
    PACKED_EXCEPTIONS = {}
    
    def __init__(self, instream, outstream):
        self._instream = instream
        self._outstream = outstream 
        self._seq = itertools.count()
    
    @classmethod
    def from_transport(cls, transport):
        return cls(transport.get_input_stream(), transport.get_output_stream())
    
    @classmethod
    def connect(cls, host, port):
        return cls.from_transport(transports.SocketTransport.connect(host, port))
    
    def close(self):
        if self._instream:
            self._instream.close()
            self._outstream.close()
            self._instream = None
            self._outstream = None

    def _decref(self, oid):
        seq = self._seq.next()
        try:
            Int32.pack(seq, self._outstream)
            Int8.pack(CMD_DECREF, self._outstream)
            Int64.pack(oid, self._outstream)
        except Exception:
            pass

    def _cmd_invoke(self, funcid):
        seq = self._seq.next()
        Int32.pack(seq, self._outstream)
        Int8.pack(CMD_INVOKE, self._outstream)
        Int32.pack(funcid, self._outstream)
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

    def _load_generic_error(self):
        msg = Str.unpack(self._instream)
        return GenericError(msg)

    def _read_reply(self, packer):
        seq = Int32.unpack(self._instream)
        code = Int8.unpack(self._instream)
        if code == REPLY_SUCCESS:
            if packer:
                return seq, packer.unpack(self._instream)
            else:
                return seq, None
        elif code == REPLY_PROTOCOL_ERROR:
            raise self._load_protocol_exception()
        elif code == REPLY_PACKED_ERROR:
            raise self._load_packed_exception()
        elif code == REPLY_GENERIC_ERROR:
            raise self._load_generic_error()
        else:
            raise ProtocolError("unknown reply code: %d" % (code,));













