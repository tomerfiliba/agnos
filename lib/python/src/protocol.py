from packers import Int8, Int32, Int64, Str
import itertools


CMD_PING = 0
CMD_INVOKE = 1
CMD_QUIT = 2
CMD_DECREF = 3

REPLY_SUCCESS = 0
REPLY_PROTOCOL_ERROR = 1
REPLY_EXECUTION_ERROR = 2

class PackedException(Exception):
    def pack(self, stream):
        raise NotImplementedError()

class ProtocolError(Exception):
    pass


class BaseProcessor(object):
    def __init__(self):
        self.cells = {}
        
    def store(self, obj):
        oid = id(obj)
        if oid in self.cells:
            ref = 1
        else:
            ref = self.cells[oid][0]
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
        Int32.pack(seq, outstream)
        Int8.pack(REPLY_EXECUTION_ERROR, outstream)
        exc.pack(outstream)
        outstream.flush()
    
    def send_protocol_error(self, outstream, seq, exc):
        Int32.pack(seq, outstream)
        Int8.pack(REPLY_PROTOCOL_ERROR, outstream)
        Str.pack(repr(exc), outstream)
        outstream.flush()
    
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
            self.send_packed_error(outstream, seq, ex)

    def process_ping(self, seq, instream, outstream):
        msg = Str.unpack(instream)
        Int32.pack(seq, outstream)
        Int8.pack(REPLY_SUCCESS, outstream)
        Str.pack(msg, outstream)
        outstream.flush()

    def process_decref(self, seq, instream, outstream):
        oid = Int64.unpack(instream)
        self.decref(oid)

    def process_quit(self, seq, instream, outstream):
        pass

    def process_invoke(self, seq, instream, outstream):
        raise NotImplementedError()


class BaseClient(object):
    def __init__(self, instream, outstream):
        self._instream = instream
        self._outstream = outstream 
        self._seq = itertools.count()
    
    def close(self):
        if self._instream:
            self._instream.close()
            self._outstream.close()
            self._instream = None
            self._outstream = None

    def _decref(oid):
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

    def _load_packed_exception():
        raise NotImplementedError()

    def _load_protocol_error():
        msg = Str.unpack(self._instream)
        return ProtocolError(msg)

    def _read_reply(packer):
        code = Int8.unpack(self._instream)
        if code == REPLY_SUCCESS:
            return packer.unpack(self._instream)
        elif code == REPLY_PROTOCOL_ERROR:
            raise self._load_protocol_exception()
        elif code == REPLY_EXECUTION_ERROR:
            raise self._load_packed_exception()
        else:
            raise ProtocolError("unknown reply code: %d" % (code,));













