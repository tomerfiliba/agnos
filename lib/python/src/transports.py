import socket
from select import select


class SocketFile(object):
    CHUNK = 8000
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
        bufs = []
        while count > 0:
            select([self.sock], [], [])
            data = self.sock.recv(min(count, self.CHUNK))
            if not data:
                raise EOFError("premature end of stream detected")
            bufs.append(data)
        return "".join(bufs)
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
    def __init__(self, file, bufsize = 8000):
        self.file = file
        self.bufsize = bufsize
        self.buffer = ""
    def close(self):
        self.file.close()
    def read(self, count):
        if len(self.buffer) >= count:
            data = self.buffer[:count]
            self.buffer = self.buffer[count:]
        else:
            req = count - len(self.buffer)
            data2 = self.file.read(max(req, self.bufsize))
            data = self.buffer + data2[:req]
            self.buffer = data2[req:]
        return data

class OutStream(object):
    def __init__(self, file, bufsize = 8000):
        self.file = file
        self.bufsize = bufsize
        self.buffer = ""
    def close(self):
        self.file.close()
    def flush(self):
        if self.buffer:
            self.file.write(buffer)
            self.buffer = ""
    def write(self, data):
        self.buffer += data
        if len(self.buffer) > self.bufsize:
            self.flush()

class SocketTransportFactory(TransportFactory):
    def __init__(self, host, port, backlog = 10):
        self.sock = socket.socket()
        self.sock.bind((host, port))
        self.sock.listen(backlog)
    def accept(self):
        return SocketTransport(self.sock.accept())

class SocketTransport(Transport):
    def __init__(self, sock):
        self.sock = SocketFile(self.sock)
    def get_input_stream(self):
        return InStream(self.sock)
    def get_output_stream(self):
        return OutStream(self.sock)






