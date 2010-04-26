using System;
using System.IO;
using System.Collections.Generic;
using Agnos;

namespace RemoteFilesAutogen
{
    public static class RemoteFiles
    {
        //
        // enums
        //
        public enum Errno
        {
            EACCES = 0,
            EBADF = 1,
            EFAULT = 2,
            ELOOP = 3,
            ENAMETOOLONG = 4,
            ENOENT = 5,
            ENOMEM = 6,
            ENOTDIR = 7,
            EEXIST = 8,
            EISDIR = 9,
            EPERM = 10,
            EROFS = 11,
            EWOULDBLOCK = 12
        }
        
        //
        // records
        //
        public class UnderlyingIOError : PackedException
        {
            protected const int __record_id = 1353;
            public string message;
            public Errno errno;
            
            public UnderlyingIOError()
            {
            }
            public UnderlyingIOError(string message, Errno errno)
            {
                this.message = message;
                this.errno = errno;
            }
            
            public override void pack(Stream stream)
            {
                Packers.Int32.pack(__record_id, stream);
                UnderlyingIOErrorRecord.pack(this, stream);
            }
            
            public override String ToString()
            {
                return "UnderlyingIOError(" + message + ", " + errno + ")";
            }
        }
        
        internal class _UnderlyingIOErrorRecord : Packers.IPacker
        {
            public void pack(object obj, Stream stream)
            {
                UnderlyingIOError val = (UnderlyingIOError)obj;
                Packers.Str.pack(val.message, stream);
                Packers.Int32.pack(val.errno, stream);
            }
            public object unpack(Stream stream)
            {
                return new UnderlyingIOError((string)Packers.Str.unpack(stream), (Errno)Packers.Int32.unpack(stream));
            }
        }
        
        internal static _UnderlyingIOErrorRecord UnderlyingIOErrorRecord = new _UnderlyingIOErrorRecord();
        
        public class StatRes
        {
            protected const int __record_id = 1369;
            public int inode;
            public int mode;
            public int size;
            public int uid;
            public int gid;
            public DateTime atime;
            public DateTime mtime;
            public DateTime ctime;
            
            public StatRes()
            {
            }
            public StatRes(int inode, int mode, int size, int uid, int gid, DateTime atime, DateTime mtime, DateTime ctime)
            {
                this.inode = inode;
                this.mode = mode;
                this.size = size;
                this.uid = uid;
                this.gid = gid;
                this.atime = atime;
                this.mtime = mtime;
                this.ctime = ctime;
            }
            
            public void pack(Stream stream)
            {
                Packers.Int32.pack(__record_id, stream);
                StatResRecord.pack(this, stream);
            }
            
            public override String ToString()
            {
                return "StatRes(" + inode + ", " + mode + ", " + size + ", " + uid + ", " + gid + ", " + atime + ", " + mtime + ", " + ctime + ")";
            }
        }
        
        internal class _StatResRecord : Packers.IPacker
        {
            public void pack(object obj, Stream stream)
            {
                StatRes val = (StatRes)obj;
                Packers.Int32.pack(val.inode, stream);
                Packers.Int32.pack(val.mode, stream);
                Packers.Int32.pack(val.size, stream);
                Packers.Int32.pack(val.uid, stream);
                Packers.Int32.pack(val.gid, stream);
                Packers.Date.pack(val.atime, stream);
                Packers.Date.pack(val.mtime, stream);
                Packers.Date.pack(val.ctime, stream);
            }
            public object unpack(Stream stream)
            {
                return new StatRes((int)Packers.Int32.unpack(stream), (int)Packers.Int32.unpack(stream), (int)Packers.Int32.unpack(stream), (int)Packers.Int32.unpack(stream), (int)Packers.Int32.unpack(stream), (DateTime)Packers.Date.unpack(stream), (DateTime)Packers.Date.unpack(stream), (DateTime)Packers.Date.unpack(stream));
            }
        }
        
        internal static _StatResRecord StatResRecord = new _StatResRecord();
        
        //
        // consts
        //
        public const int S_IFREG = 1048576;
        public const int S_IFBLK = 393216;
        public const int S_IFDIR = 262144;
        public const int S_IFIFO = 65536;
        public const int S_IFLNK = 1179648;
        public const int S_IFCHR = 131072;
        
        //
        // classes
        //
        public abstract class BaseProxy : IDisposable
        {
            internal long _objref;
            protected Client _client;
            protected bool _disposed;
            
            protected BaseProxy(Client client, long objref)
            {
                _client = client;
                _objref = objref;
                _disposed = false;
            }
            
            ~BaseProxy()
            {
                Dispose(false);
            }
            
            public void Dispose()
            {
                Dispose(true);
                GC.SuppressFinalize(this);
            }
            private void Dispose(bool disposing)
            {
                if (_disposed)
                {
                    return;
                }
                lock (this)
                {
                    _disposed = true;
                    _client._decref(_objref);
                }
            }
            
            public override String ToString()
            {
                return base.ToString() + "<" + _objref + ">";
            }
        }
        
        public interface IFile
        {
            // attributes
            string filename
            {
                get;
            }
            
            // methods
            StatRes stat();
            byte[] read(int count);
            void write(byte[] data);
            void close();
            void flush();
        }
        
        public class FileProxy : BaseProxy
        {
            internal FileProxy(Client client, long objref) : base(client, objref)
            {
            }
            
            public string filename
            {
                get
                {
                    return _client._File_get_filename(this);
                }
            }
            
            public StatRes stat()
            {
                return _client._File_stat(this);
            }
            public byte[] read(int count)
            {
                return _client._File_read(this, count);
            }
            public void write(byte[] data)
            {
                _client._File_write(this, data);
            }
            public void close()
            {
                _client._File_close(this);
            }
            public void flush()
            {
                _client._File_flush(this);
            }
        }
        
        public interface IPath
        {
            
            // methods
            bool isDir();
            bool isFile();
            IPath append(IPath other);
            IPath up();
        }
        
        public class PathProxy : BaseProxy
        {
            internal PathProxy(Client client, long objref) : base(client, objref)
            {
            }
            
            
            public bool isDir()
            {
                return _client._Path_isDir(this);
            }
            public bool isFile()
            {
                return _client._Path_isFile(this);
            }
            public PathProxy append(PathProxy other)
            {
                return _client._Path_append(this, other);
            }
            public PathProxy up()
            {
                return _client._Path_up(this);
            }
        }
        
        //
        // server implementation
        //
        public interface IHandler
        {
            void copy(IFile src, IFile dst);
            IFile open(string filename, string mode);
        }
        
        public class Processor : Protocol.BaseProcessor
        {
            protected IHandler handler;
            
            public Processor(IHandler handler) : base()
            {
                this.handler = handler;
            }
            
            protected override void process_invoke(Stream inStream, Stream outStream, int seq)
            {
                int funcid = (int)Packers.Int32.unpack(inStream);
                Packers.IPacker packer = null;
                object result = null;
                long id;
                switch (funcid)
                {
                    case 1398:
                        id = (long)(Packers.Int64.unpack(inStream));
                        result = ((IPath)load(id)).isDir();
                        packer = Packers.Bool;
                        break;
                    case 1392:
                        id = (long)(Packers.Int64.unpack(inStream));
                        result = ((IFile)load(id)).filename;
                        packer = Packers.Str;
                        break;
                    case 1396:
                        id = (long)(Packers.Int64.unpack(inStream));
                        ((IFile)load(id)).close();
                        break;
                    case 1397:
                        id = (long)(Packers.Int64.unpack(inStream));
                        ((IFile)load(id)).flush();
                        break;
                    case 1399:
                        id = (long)(Packers.Int64.unpack(inStream));
                        result = ((IPath)load(id)).isFile();
                        packer = Packers.Bool;
                        break;
                    case 1393:
                        id = (long)(Packers.Int64.unpack(inStream));
                        result = ((IFile)load(id)).stat();
                        packer = StatResRecord;
                        break;
                    case 1395:
                        id = (long)(Packers.Int64.unpack(inStream));
                        ((IFile)load(id)).write((byte[])(Packers.Buffer.unpack(inStream)));
                        break;
                    case 1401:
                        id = (long)(Packers.Int64.unpack(inStream));
                        result = ((IPath)load(id)).up();
                        result = store(result);
                        packer = Packers.Int64;
                        break;
                    case 1394:
                        id = (long)(Packers.Int64.unpack(inStream));
                        result = ((IFile)load(id)).read((int)(Packers.Int32.unpack(inStream)));
                        packer = Packers.Buffer;
                        break;
                    case 1390:
                        handler.copy((IFile)(load((long)Packers.Int64.unpack(inStream))), (IFile)(load((long)Packers.Int64.unpack(inStream))));
                        break;
                    case 1387:
                        result = handler.open((string)(Packers.Str.unpack(inStream)), (string)(Packers.Str.unpack(inStream)));
                        result = store(result);
                        packer = Packers.Int64;
                        break;
                    case 1400:
                        id = (long)(Packers.Int64.unpack(inStream));
                        result = ((IPath)load(id)).append((IPath)(load((long)Packers.Int64.unpack(inStream))));
                        result = store(result);
                        packer = Packers.Int64;
                        break;
                    default:
                        throw new ProtocolError("unknown function id: " + funcid);
                }
                
                Packers.Int32.pack(seq, outStream);
                Packers.Int8.pack((byte)Agnos.Protocol.REPLY_SUCCESS, outStream);
                if (packer != null)
                {
                    packer.pack(result, outStream);
                }
                outStream.Flush();
            }
        }
        
        //
        // client
        //
        public class Client : Protocol.BaseClient
        {
            public Client(Stream inStream, Stream outStream) : base(inStream, outStream)
            {
            }
            public Client(Agnos.Transports.ITransport transport) : base(transport)
            {
            }
            
            internal new void _decref(long id)
            {
                base._decref(id);
            }
            
            protected override PackedException _load_packed_exception()
            {
                int clsid = (int)Packers.Int32.unpack(_inStream);
                switch (clsid)
                {
                    case 1353:
                        return (PackedException)(UnderlyingIOErrorRecord.unpack(_inStream));
                    default:
                        throw new ProtocolError("unknown exception class id: " + clsid);
                }
            }
            
            internal bool _Path_isDir(PathProxy _proxy)
            {
                _cmd_invoke(1398);
                Packers.Int64.pack(_proxy._objref, _outStream);
                _outStream.Flush();
                object res = _read_reply(Packers.Bool);
                return (bool)res;
            }
            internal string _File_get_filename(FileProxy _proxy)
            {
                _cmd_invoke(1392);
                Packers.Int64.pack(_proxy._objref, _outStream);
                _outStream.Flush();
                object res = _read_reply(Packers.Str);
                return (string)res;
            }
            internal void _File_close(FileProxy _proxy)
            {
                _cmd_invoke(1396);
                Packers.Int64.pack(_proxy._objref, _outStream);
                _outStream.Flush();
                _read_reply(null);
            }
            internal void _File_flush(FileProxy _proxy)
            {
                _cmd_invoke(1397);
                Packers.Int64.pack(_proxy._objref, _outStream);
                _outStream.Flush();
                _read_reply(null);
            }
            internal bool _Path_isFile(PathProxy _proxy)
            {
                _cmd_invoke(1399);
                Packers.Int64.pack(_proxy._objref, _outStream);
                _outStream.Flush();
                object res = _read_reply(Packers.Bool);
                return (bool)res;
            }
            internal StatRes _File_stat(FileProxy _proxy)
            {
                _cmd_invoke(1393);
                Packers.Int64.pack(_proxy._objref, _outStream);
                _outStream.Flush();
                object res = _read_reply(StatResRecord);
                return (StatRes)res;
            }
            internal void _File_write(FileProxy _proxy, byte[] data)
            {
                _cmd_invoke(1395);
                Packers.Int64.pack(_proxy._objref, _outStream);
                Packers.Buffer.pack(data, _outStream);
                _outStream.Flush();
                _read_reply(null);
            }
            internal PathProxy _Path_up(PathProxy _proxy)
            {
                _cmd_invoke(1401);
                Packers.Int64.pack(_proxy._objref, _outStream);
                _outStream.Flush();
                object res = _read_reply(Packers.Int64);
                return new PathProxy(this, (long)res);
            }
            internal byte[] _File_read(FileProxy _proxy, int count)
            {
                _cmd_invoke(1394);
                Packers.Int64.pack(_proxy._objref, _outStream);
                Packers.Int32.pack(count, _outStream);
                _outStream.Flush();
                object res = _read_reply(Packers.Buffer);
                return (byte[])res;
            }
            public void copy(FileProxy src, FileProxy dst)
            {
                _cmd_invoke(1390);
                Packers.Int64.pack(src._objref, _outStream);
                Packers.Int64.pack(dst._objref, _outStream);
                _outStream.Flush();
                _read_reply(null);
            }
            public FileProxy open(string filename, string mode)
            {
                _cmd_invoke(1387);
                Packers.Str.pack(filename, _outStream);
                Packers.Str.pack(mode, _outStream);
                _outStream.Flush();
                object res = _read_reply(Packers.Int64);
                return new FileProxy(this, (long)res);
            }
            internal PathProxy _Path_append(PathProxy _proxy, PathProxy other)
            {
                _cmd_invoke(1400);
                Packers.Int64.pack(_proxy._objref, _outStream);
                Packers.Int64.pack(other._objref, _outStream);
                _outStream.Flush();
                object res = _read_reply(Packers.Int64);
                return new PathProxy(this, (long)res);
            }
        }
        
    }
}