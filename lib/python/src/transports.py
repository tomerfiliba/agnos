class Transport(object):
    def open(self):
        pass
    def close(self):
        pass
    def read(self, count):
        pass
    def write(self, count):
        pass
    def flush(self):
        pass

class TransportFactory(object):
    def open(self):
        pass
    def close(self):
        pass
    def accept(self):
        pass

class Socket(Transport):
    def __init__(self, sock):
        self.sock = sock
    def open(self):
        self.sock.connect((0,0))
    def close(self):
        self.sock.close()
    def read(self, count):
        return self.sock.read(count)
    def write(self, data):
        while data:
            count = self.sock.send(data[:4000])
            data = data[count:]

class SocketFactory(object):
    def __init__(self, port = 0, host = None, backlog = 8):
        self.port = port
        self.host = host
        self.backlog = backlog
        self.sock = socket.socket()
    def open(self):
        self.sock.bind((self.host, self.port))
        self.sock.listen(self.backlog)
    def close(self):
        self.sock.close()
    def accept(self):
        return Socket.wrap(self.sock.accept()[0])







