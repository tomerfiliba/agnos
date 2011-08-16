##############################################################################
# Part of the Agnos RPC Framework
#    http://agnos.sourceforge.net
#
# Copyright 2011, International Business Machines Corp.
#                 Author: Tomer Filiba (tomerf@il.ibm.com)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
##############################################################################

import socket
import ssl
import signal
import time
from select import select
try:
    from cStringIO import StringIO
except ImportError:
    from io import StringIO
from contextlib import contextmanager
from subprocess import Popen, PIPE
from . import packers
from .utils import RLock, BoundedStream, ZlibStream
try:
    from zlib import compress as zlib_compress
except ImportError:
    zlib_compress = None


class TransportTimeout(IOError):
    pass

class _DebugFile(object):
    def __init__(self, fileobj):
        self.fileobj = fileobj
    def write(self, data):
        import sys, os
        print >>sys.stderr, "%05d W %r" % (os.getpid(), data)
        self.fileobj.write(data)
    def read(self, count):
        import sys, os
        data = self.fileobj.read(count)
        print >>sys.stderr, "%05d R %r" % (os.getpid(), data)
        return data
    def flush(self):
        self.fileobj.flush()
    def close(self):
        self.fileobj.close()


class Transport(object):
    """
    a transport is a thread-safe, compression-aware, transaction-based, 
    file-like object that supports up to a single ongoing write transaction 
    and a single ongoing read transaction. it operates over two file-like 
    objects (one for input and the other for output), which may be the same 
    e.g., in the case of sockets.
    """
    
    def __init__(self, infile, outfile):
        self.infile = infile
        #self.outfile = _DebugFile(outfile)
        self.outfile = outfile
        self.compression_threshold = -1
        self._rlock = RLock()
        self._wlock = RLock()
        self._wseq = -1
        self._wbuffer = []
        self._rstream = None
    
    def is_compression_enabled(self):
        """returns whether compression is enabled on this transport"""
        return self.compression_threshold > 0
    def enabled_compression(self):
        """
        attempts to enable compression on this transport, and returns whether 
        compression has been enabled. note that not all transport implementation
        support compression, and not all implementations of libagnos support
        compression. before calling this method, be sure to test that the other
        party reports True under "COMPRESSION_SUPPOTED" in INFO_META.
        """
        self.compression_threshold = zlib_compress is not None and self._get_compression_threshold()
        return self.is_compression_enabled()
    def disable_compresion(self):
        """disables compression on this transport"""
        self.compression_threshold = -1
    def _get_compression_threshold(self):
        """returns the compression threshold to be used on this transport. 
        packets larger than this threshold will be compressed. a negative value
        means compression is not supported"""
        return -1
    
    def close(self):
        if self.infile:
            self.infile.close()
            self.infile = None
        if self.outfile:
            self.outfile.close()
            self.outfile = None
    
    def fileno(self):
        return self.infile.fileno()
    
    def begin_read(self, timeout = None):
        """
        begins a read transaction. only a single thread can have an ongoing read
        transaction. other threads calling this method will block until the 
        ongoing transaction ends. this method will also block until enough
        data is received to begin the transaction, unless timeout is specified.
        be sure to call end_read when done.
        """
        if self._rlock.is_held_by_current_thread():
            raise IOError("begin_read is not reentrant")
        self._rlock.acquire()
        try:
            if timeout is not None and timeout < 0:
                timeout = 0
            if not select([self.infile], [], [], timeout)[0]:
                self._rlock.release()
                raise TransportTimeout("no data received within %r seconds" % (timeout,))
            
            seq = packers.Int32.unpack(self.infile)
            packet_length = packers.Int32.unpack(self.infile)
            uncompressed_length = packers.Int32.unpack(self.infile)
            
            assert self._rstream is None

            self._rstream = BoundedStream(self.infile, packet_length, 
                skip_underlying = True, close_underlying = False)
            
            if uncompressed_length > 0:
                self._rstream = BoundedStream(ZlibStream(self._rstream), 
                    uncompressed_length, skip_underlying = False, 
                    close_underlying = True)

            return seq
        except Exception:
            self._rstream = None
            self._rlock.release()
            raise
    
    def _assert_rlock(self):
        if not self._rlock.is_held_by_current_thread():
            raise IOError("thread must first call begin_read")
    
    def read(self, count):
        """reads up to `count` bytes from the ongoing read transaction. 
        begin_read() must have been called prior to this"""
        self._assert_rlock()
        if count > self._rstream.available():
            raise EOFError("request to read more than available")
        return self._rstream.read(count)
    
    def read_all(self):
        """reads all the available data in the ongoing read transaction.
        begin_read() must have been called prior to this"""
        self._assert_rlock()
        return self._rstream.read()
    
    def end_read(self):
        """ends the ongoing read transaction. begin_read() must have been 
        called prior to this. you must call this to finalize the transaction"""
        self._assert_rlock()
        if self._rstream is not None:
            self._rstream.close()
            self._rstream = None
        self._rlock.release()
    
    def begin_write(self, seq):
        """begins a write transaction. only a single thread can have an ongoing
        write transaction. other threads calling this method will block until
        the ongoing transaction ends. end_write() or cancel_write() must be
        called to finalize the transaction.
        """
        if self._wlock.is_held_by_current_thread():
            raise IOError("begin_write() is not reentrant")
        self._wlock.acquire()
        self._wseq = seq
        del self._wbuffer[:]
    
    def _assert_wlock(self):
        if not self._wlock.is_held_by_current_thread():
            raise IOError("thread must first call begin_write()")
    
    def write(self, data):
        """writes the given data to the transaction buffer (non-blocking).
        begin_write must have been called prior to this"""
        self._assert_wlock()
        self._wbuffer.append(data)
    
    def restart_write(self):
        """clears the transaction buffer (non-blocking), effectively restarting
        the write transaction. begin_write must have been called prior to this"""
        self._assert_wlock()
        del self._wbuffer[:]
    
    def end_write(self):
        """finalizes the transaction and flushes all the write buffer to the 
        underlying stream. begin_write must have been called prior to this.
        must be called to finalize the transaction"""
        self._assert_wlock()
        data = "".join(self._wbuffer)
        del self._wbuffer[:]
        if data:
            packers.Int32.pack(self._wseq, self.outfile)
            if self.compression_threshold > 0 and len(data) > self.compression_threshold:
                uncompressed_length = len(data)
                data = zlib_compress(data)
            else:
                uncompressed_length = 0
            packers.Int32.pack(len(data), self.outfile)
            packers.Int32.pack(uncompressed_length, self.outfile)
            self.outfile.write(data)
            self.outfile.flush()
        self._wlock.release()
    
    def cancel_write(self):
        """finalizes the transaction and WITHOUT writing anything to the 
        underlying stream. allows one to cancel an ongoing write transaction. 
        begin_write must have been called prior to this. do not call end_write
        after canceling the transaction"""
        self._assert_wlock()
        del self._wbuffer[:]
        self._wlock.release()
    
    @contextmanager
    def reading(self, timeout = None):
        """a convenience context that takes care of begin_read and end_read"""
        seq = self.begin_read(timeout)
        try:
            yield seq
        finally:
            self.end_read()

    @contextmanager
    def writing(self, seq):
        """a convenience context that takes care of begin_write and end_write.
        will cancel the transaction in case of an exception"""
        self.begin_write(seq)
        try:
            yield
        except Exception:
            self.cancel_write()
            raise
        else:
            self.end_write()


class WrappedTransport(object):
    """a transport that wraps an underlying transport object"""
    def __init__(self, transport):
        self.transport = transport
    def __repr__(self):
        return "WrappedTransport(%s)" % (self.transport,)
    def is_compression_enabled(self):
        return self.transport.is_compression_enabled()
    def enabled_compression(self):
        return self.transport.enabled_compression()
    def disable_compresion(self):
        self.transport.disable_compresion()
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
    def restart_write(self):
        return self.transport.restart_write()
    def end_write(self):
        return self.transport.end_write()
    def cancel_write(self):
        return self.transport.cancel_write()
    def reading(self, timeout = None):
        return self.transport.reading(timeout)
    def writing(self, seq):
        return self.transport.writing(seq)


class SocketFile(object):
    """file-like wrapper for sockets"""
    
    CHUNK = 16*1024
    def __init__(self, sock, read_buffer_size = 64*1024):
        self.sock = sock
        self.sock_host, self.sock_port = sock.getsockname()
        self.peer_host, self.peer_port = sock.getpeername()
        self.sock.setblocking(False)
        self.read_buffer_size = read_buffer_size
        self.read_buffer = ""

    @classmethod
    def connect(cls, host, port):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
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
            select([], [self.sock], [], None) # wait until writable
            sent = self.sock.send(buf)
            data = data[sent:]


class SocketTransport(Transport):
    """implementation of a socket-backed transport"""
    def __init__(self, sockfile):
        Transport.__init__(self, sockfile, sockfile)
    def __repr__(self):
        return "<SocketTransport %s:%s - %s:%s>" % (self.infile.sock_host, 
            self.infile.sock_port, self.infile.peer_host, self.infile.peer_port)
    
    def _get_compression_threshold(self):
        return 4 * 1024
    
    @classmethod
    def connect(cls, host, port):
        return cls(SocketFile.connect(host, port))
    @classmethod
    def from_socket(cls, sock):
        return cls(SocketFile(sock))


class SslSocketTransport(Transport):
    """implementation of an SSL socket-backed transport"""
    def __init__(self, sslsockfile):
        Transport.__init__(self, sslsockfile, sslsockfile)
    def __repr__(self):
        return "<SslSocketTransport %s:%s - %s:%s>" % (self.infile.sock_host, 
            self.infile.sock_port, self.infile.peer_host, self.infile.peer_port)
    
    @classmethod
    def connect(cls, host, port, keyfile = None, certfile = None,  
            cert_reqs = ssl.CERT_NONE, **kwargs):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sslsock = ssl.wrap_socket(sock, keyfile = keyfile, certfile = certfile,
            server_side = False, cert_reqs = cert_reqs, **kwargs)
        sslsock.connect((host, port))
        return cls(SocketFile(sslsock))
    @classmethod
    def from_ssl_socket(cls, sslsock):
        return cls(SocketFile(sslsock))


class ProcTransport(WrappedTransport):
    """an implementation of a process-backed transport. spawns a server (as a
    child processor) and connects to it. the child process is expected to die
    when the connection is closed. to create, use the from_executable() or
    from_proc() factory methods.
    """
    
    def __init__(self, proc, transport):
        WrappedTransport.__init__(self, transport)
        self.proc = proc
    def __repr__(self):
        return "<ProcTransport pid=%s (%s)>" % (self.proc.pid, "alive" if self.proc.poll() is None else "terminated")
    
    def close(self, grace_period = 0.7):
        """closes the transport and kills the child process, should it not die
        within the given grace period"""
        WrappedTransport.close(self)
        self.proc.send_signal(signal.SIGINT)
        tend = time.time() + grace_period
        while self.proc.poll() is None and time.time() <= tend:
            time.sleep(0.1)
        if self.proc.poll() is None:
            self.proc.terminate()
    
    def enable_compression(self):
        return False
    
    @classmethod
    def from_executable(cls, filename, args = ("-m", "lib")):
        """spawn the given executable wit the given arguments. expected to be 
        a library-mode Agnos server"""
        if isinstance(filename, str):
            cmdline = [filename]
        else:
            cmdline = filename
        cmdline.extend(args)
        proc = Popen(cmdline, shell = False, stdin = PIPE, stdout = PIPE)
        return cls.from_proc(proc)

    @classmethod
    def from_proc(cls, proc):
        """connect to a running subprocess.Popen instance"""
        if proc.poll() is not None:
            raise ValueError("process terminated with exit code %r" % (proc.poll(),))
        if proc.stdout.readline().strip() != "AGNOS":
            raise ValueError("process did not start correctly")
        host = proc.stdout.readline().strip()
        port = int(proc.stdout.readline().strip())
        proc.stdout.close()
        transport = SocketTransport.connect(host, port)
        return cls(proc, transport)


#===============================================================================
# transport factory
#===============================================================================

class TransportFactory(object):
    """transport factory"""
    
    def accept(self):
        """accepts and returns a new Transport instance. blocks until one 
        arrives"""
        raise NotImplementedError()
    def close(self):
        """closes the transport factory (i.e., the listening socket)"""
        raise NotImplementedError()
    def fileno(self):
        """returns the file descriptor (to allow passing this to select())"""
        raise NotImplementedError()


class SocketTransportFactory(TransportFactory):
    """socket-backed transport factory"""
    
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
    def fileno(self):
        return self.sock.fileno()


class SslSocketTransportFactory(TransportFactory):
    """SSL socket-backed transport factory"""

    def __init__(self, port, keyfile, certfile, host = "0.0.0.0", backlog = 10, **kwargs):
        self.sock = socket.socket()
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((host, port))
        self.sock.listen(backlog)
        self.host, self.port = self.sock.getsockname()
        self.ssl_options = dict(keyfile = keyfile, certfile = certfile, 
            server_side = True, **kwargs)
    
    def accept(self):
        sock2 = self.sock.accept()[0]
        sslsock = ssl.wrap_socket(sock2, **self.ssl_options)
        return SslSocketTransport.from_ssl_socket(sslsock)
    
    def close(self):
        self.sock.close()

    def fileno(self):
        return self.sock.fileno()






