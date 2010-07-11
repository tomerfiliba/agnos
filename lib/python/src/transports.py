import socket
import signal
import time
from select import select
from contextlib import contextmanager
from subprocess import Popen, PIPE
from . import packers
from .utils import RLock 


class TransportTimeout(IOError):
    pass

class Transport(object):
    def __init__(self, infile, outfile):
        self.infile = infile
        self.outfile = outfile
        self._rlock = RLock()
        self._wlock = RLock()
        self._read_length = -1
        self._read_pos = -1
        self._read_seq = -1
        self._write_seq = -1
        self._write_buffer = []
    
    def close(self):
        if self.infile:
            self.infile.close()
            self.infile = None
        if self.outfile:
            self.outfile.close()
            self.outfile = None
    
    def begin_read(self, timeout = None):
        if self._rlock.is_held_by_current_thread():
            raise IOError("begin_read is not reentrant")
        self._rlock.acquire()
        if timeout is not None and timeout < 0:
            timeout = 0
        rl, _, _ = select([self.infile], [], [], timeout)
        if not rl:
            self._rlock.release()
            raise TransportTimeout("no data received within %r seconds" % (timeout,))
        self._read_length = packers.Int32.unpack(self.infile)
        self._read_seq = packers.Int32.unpack(self.infile)
        self._read_pos = 0
        return self._read_seq
    
    def read(self, count):
        if not self._rlock.is_held_by_current_thread():
            raise IOError("thread must first call begin_read")
        if self._read_pos + count > self._read_length:
            raise EOFError("request to read more than available")
        data = self.infile.read(count)
        self._read_pos += len(data)
        return data
    
    def read_all(self):
        return self.read(self._read_length - self._read_pos)
    
    def end_read(self):
        if not self._rlock.is_held_by_current_thread():
            raise IOError("thread must first call begin_read")
        remaining = self._read_length - self._read_pos
        while remaining > 0:
            chunk = self.infile.read(min(remaining, 16*1024))
            remaining -= len(chunk)
        self._rlock.release()
    
    def begin_write(self, seq):
        if self._wlock.is_held_by_current_thread():
            raise IOError("begin_write is not reentrant")
        self._wlock.acquire()
        self._write_seq = seq
        del self._write_buffer[:]
    
    def write(self, data):
        if not self._wlock.is_held_by_current_thread():
            raise IOError("thread must first call begin_write")
        self._write_buffer.append(data)
    
    def reset(self):
        if not self._wlock.is_held_by_current_thread():
            raise IOError("thread must first call begin_write")
        del self._write_buffer[:]
    
    def end_write(self):
        if not self._wlock.is_held_by_current_thread():
            raise IOError("thread must first call begin_write")
        data = "".join(self._write_buffer)
        del self._write_buffer[:]
        if data:
            packers.Int32.pack(len(data), self.outfile)
            packers.Int32.pack(self._write_seq, self.outfile)
            self.outfile.write(data)
            self.outfile.flush()
        self._wlock.release()
    
    def cancel_write(self):
        if not self._wlock.is_held_by_current_thread():
            raise IOError("thread must first call begin_write")
        del self._write_buffer[:]
        self._wlock.release()
    
    @contextmanager
    def reading(self, timeout = None):
        yield self.begin_read(timeout)
        self.end_read()

    @contextmanager
    def writing(self, seq):
        self.begin_write(seq)
        yield
        self.end_write()


class WrappedTransport(object):
    def __init__(self, transport):
        self.transport = transport
    def close(self):
        return self.transport.close()
    def begin_read(self, timeout = None):
        return self.transport.begin_read(timeout)
    def read(self, count):
        return self.transport.read(count)
    def read_all(self):
        return self.transport.read_all()
    def begin_write(self, seq):
        return self.transport.begin_write(seq)
    def write(self, data):
        return self.transport.write(data)
    def reset(self):
        return self.transport.reset()
    def end_write(self):
        return self.transport.end_write()
    def cancel_write(self):
        return self.transport.cancel_write()
    def reading(self, timeout = None):
        return self.transport.reading(timeout)
    def writing(self, seq):
        return self.transport.writing(seq)


class SocketFile(object):
    CHUNK = 16*1024
    def __init__(self, sock, read_buffer_size = 64*1024):
        self.sock = sock
        self.sock.setblocking(False)
        self.read_buffer_size = read_buffer_size
        self.read_buffer = ""
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
    
    def _underlying_read(self, count):
        bufs = []
        upper_count = count + self.read_buffer_size
        timeout = None
        while upper_count > 0:
            rl = select([self.sock], [], [], timeout)[0]
            if not rl:
                break
            data = self.sock.recv(min(upper_count, self.CHUNK))
            if not data:
                break
            bufs.append(data)
            if timeout == 0:
                break
            count -= len(data)
            upper_count -= len(data)
            if count < 0:
                timeout = 0
        return "".join(bufs)
    
    def read(self, count):
        if len(self.read_buffer) >= count:
            data = self.read_buffer[:count]
            self.read_buffer = self.read_buffer[count:]
        else:
            req = count - len(self.read_buffer)
            data2 = self._underlying_read(req)
            data = self.read_buffer + data2[:req]
            self.read_buffer = data2[req:]
        if count > 0 and not data:
            raise EOFError()
        return data
    
    def write(self, data):
        while data:
            buf = data[:self.CHUNK]
            sent = self.sock.send(buf)
            data = data[sent:]


class SocketTransport(Transport):
    def __init__(self, sockfile):
        Transport.__init__(self, sockfile, sockfile)
    @classmethod
    def connect(cls, host, port):
        return cls(SocketFile.connect(host, port))
    @classmethod
    def from_socket(cls, sock):
        return cls(SocketFile(sock))


class ProcTransport(WrappedTransport):
    def __init__(self, proc, transport):
        WrappedTransport.__init__(self, transport)
        self.proc = proc
    
    def close(self):
        WrappedTransport.close(self)
        self.proc.send_signal(signal.SIGINT)
        tend = time.time() + 0.5
        while self.proc.poll() is None and time.time() <= tend:
            time.sleep(0.1)
        if self.proc.poll() is None:
            self.proc.terminate()
    
    @classmethod
    def from_executable(cls, filename, args = ("-m", "lib")):
        if isinstance(filename, str):
            cmdline = [filename]
        else:
            cmdline = filename 
        cmdline.extend(args)
        proc = Popen(cmdline, shell = False, stdin = PIPE, stdout = PIPE)
        return cls.from_proc(proc)

    @classmethod
    def from_proc(cls, proc):
        if proc.poll() is not None:
            raise ValueError("process terminated with exit code %r" % (proc.poll(),))
        host = proc.stdout.readline().strip()
        port = int(proc.stdout.readline().strip())
        proc.stdout.close()
        transport = SocketTransport.connect(host, port)
        return cls(proc, transport)


#===============================================================================
# transport factory
#===============================================================================

class TransportFactory(object):
    def accept(self):
        raise NotImplementedError()
    def close(self):
        raise NotImplementedError()


class SocketTransportFactory(TransportFactory):
    def __init__(self, port, host = "0.0.0.0", backlog = 10):
        self.sock = socket.socket()
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((host, port))
        self.sock.listen(backlog)
        self.host, self.port = self.sock.getsockname()
    def accept(self):
        return SocketTransport.from_socket(self.sock.accept()[0])
    def close(self):
        self.sock.close()








