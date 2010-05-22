import sys
import os
import socket
from select import select
from contextlib import contextmanager
from subprocess import Popen, PIPE


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
    def flush(self):
        pass
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
        #print >>sys.stderr, "%05d  R %r" % (os.getpid(), data)
        return data
    def poll(self, timeout):
        rl, _, _ = select([self.file], [], [], timeout)
        return bool(rl)  

class TransactionCanceled(Exception):
    pass

class OutStreamTransaction(object):
    def __init__(self, stream):
        self.stream = stream
        self.buffer = []
    def clear(self):
        del self.buffer[:]
    def cancel(self):
        raise TransactionCanceled()
    def write(self, data):
        self.buffer.append(data)
    def flush(self):
        #for data in self.buffer:
        #    print >>sys.stderr, "%05d  W %r" % (os.getpid(), data)
        self.stream.write("".join(self.buffer))

class OutStream(object):
    def __init__(self, file):
        self.file = file
    def close(self):
        self.file.close()
    def write(self, data):
        self.file.write(data)
        self.file.flush()
    
    @contextmanager
    def transaction(self):
        try:
            trans = OutStreamTransaction(self)
            yield trans
        except TransactionCanceled:
            pass
        else:
            trans.flush()

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
    def __init__(self, sockfile):
        self.sock = sockfile
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

class ProcTransport(Transport):
    def __init__(self, proc, transport):
        self.proc = proc
        self.transport = transport
    def get_input_stream(self):
        return self.transport.get_input_stream()
    def get_output_stream(self):
        return self.transport.get_output_stream()
    
    @classmethod
    def from_executable(cls, filename, args = None):
        if args is None:
            args = ["-m", "-lib"]
        cmdline = [filename]
        cmdline.extend(args)
        proc = Popen(cmdline, shell = False, stdin = PIPE, stdout = PIPE)
        return cls.from_proc(proc)

    @classmethod
    def from_proc(cls, proc):
        host = proc.stdout.readline().strip()
        port = int(proc.stdout.readline().strip())
        proc.stdout.close()
        transport = SocketTransport.connect(host, port)
        return cls(proc, transport)






