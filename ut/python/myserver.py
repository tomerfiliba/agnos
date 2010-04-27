import sys
sys.path.append("..")

import os
import errno
from datetime import datetime

from agnos import SocketTransportFactory 
from agnos.servers import SimpleServer
import RemoteFiles_bindings as RemoteFiles


class FileImp(object):
    def __init__(self, filename, mode):
        self._file = open(filename, mode)
        self.filename = filename
    
    def read(self, count):
        try:
            return self._file.read(count)
        except IOError, ex:
            raise RemoteFiles.UnderlyingIOError(ex.strerror, RemoteFiles.Errno.get_by_name(errno.errorcode[ex.errno]))
    def write(self, data):
        try:
            return self._file.write(data)
        except IOError, ex:
            raise RemoteFiles.UnderlyingIOError(ex.strerror, RemoteFiles.Errno.get_by_name(errno.errorcode[ex.errno]))
    def close(self):
        self._file.close()
    def flush(self):
        try:
            self._file.flush()
        except IOError, ex:
            raise RemoteFiles.UnderlyingIOError(ex.strerror, RemoteFiles.Errno.get_by_name(errno.errorcode[ex.errno]))
    def stat(self):
        try:
            res = os.fstat(self._file.fileno())
        except IOError, ex:
            raise RemoteFiles.UnderlyingIOError(ex.strerror, RemoteFiles.Errno.get_by_name(errno.errorcode[ex.errno]))
        
        return RemoteFiles.StatRes(inode = res.st_ino, mode = res.st_mode,
            size = res.st_size, uid = res.st_uid, gid = res.st_gid,
            atime = datetime.fromtimestamp(res.st_atime),
            ctime = datetime.fromtimestamp(res.st_mtime),
            mtime = datetime.fromtimestamp(res.st_ctime))


class Handler(RemoteFiles.IHandler):
    def open(self, filename, mode):
        return FileImp(filename, mode)
    
    def copy(self, src, dst):
        while True:
            buf = src.read(16000)
            if not buf:
                break
            dst.write(buf)
        dst.flush()


if __name__ == "__main__":
    s = SimpleServer(RemoteFiles.Processor(Handler()), SocketTransportFactory(17731))
    try:
        s.serve()
    except KeyboardInterrupt:
        pass

