import sys
import os
import socket
from select import select
from contextlib import contextmanager


class SocketFile(object):
    CHUNK = 16000
    def __init__(self, sock):
        self.sock = sock
        self.sock.setblocking(False)
    @classmethod
    def connect(cls, host, port):
        s = socket.socket()
        s.connect((host, port))
        return cls(s)
    def close(self):
        self.sock.close()
    def fileno(self):
        return self.sock.fileno()
    def read(self, count):
        select([self.sock], [], [])
        return self.sock.recv(min(count, self.CHUNK))
    def write(self, data):
        while data:
            buf = data[:self.CHUNK]
            sent = self.sock.send(buf)
            data = data[sent:]


class Transport(object):
    def getInputStream(self):
        raise NotImplementedError()
    def getOutputStream(self):
        raise NotImplementedError()

class TransportFactory(object):
    def accept(self):
        raise NotImplementedError()

class InStream(object):
    def __init__(self, file, bufsize = 32000):
        self.file = file
        self.bufsize = bufsize
        self.buffer = ""
    def close(self):
        self.file.close()
    def _read(self, count):
        bufs = []
        while count > 0:
            data = self.file.read(max(count, self.bufsize))
            if not data:
                raise EOFError("premature end of stream detected")
            bufs.append(data)
            count -= len(data)
        return "".join(bufs)
    def read(self, count):
        if len(self.buffer) >= count:
            data = self.buffer[:count]
            self.buffer = self.buffer[count:]
        else:
            req = count - len(self.buffer)
            data2 = self._read(req)
            data = self.buffer + data2[:req]
            self.buffer = data2[req:]
        #print >>sys.stderr, "%05d  R %s" % (os.getpid(), data.encode("hex"))
        return data
    def poll(self, timeout):
        rl, _, _ = select([self.file], [], [], timeout)
        return bool(rl)  

class OutStream(object):
    def __init__(self, file):
        self.file = file
        self.buffer = []
        self.in_transaction = False
    def close(self):
        self.file.close()
    def write(self, data):
        assert self.in_transaction
        self.buffer.append(data)
        #print >>sys.stderr, "%05d  W %s" % (os.getpid(), data.encode("hex"))
    def flush(self):
        if not self.buffer:
            return
        data = "".join(self.buffer)
        self.file.write(data)
        del self.buffer[:]
    
    @contextmanager
    def transaction(self):
        assert not self.in_transaction
        self.in_transaction = True
        try:
            yield
            self.flush()
        finally:
            self.in_transaction = False

class SocketTransportFactory(TransportFactory):
    def __init__(self, port, host = "0.0.0.0", backlog = 10):
        self.sock = socket.socket()
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((host, port))
        self.sock.listen(backlog)
        self.host, self.port = self.sock.getsockname()
    def accept(self):
        return SocketTransport.from_socket(self.sock.accept()[0])

class SocketTransport(Transport):
    def __init__(self, sock):
        self.sock = sock
    @classmethod
    def connect(cls, host, port):
        return cls(SocketFile.connect(host, port))
    @classmethod
    def from_socket(cls, sock):
        return cls(SocketFile(sock))
    def get_input_stream(self):
        return InStream(self.sock)
    def get_output_stream(self):
        return OutStream(self.sock)






