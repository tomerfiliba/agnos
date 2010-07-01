using System;
using System.IO;
using System.Net;
using System.Net.Sockets;
using System.Diagnostics;
using Agnos.Utils;


namespace Agnos.Transports
{
    public interface ITransport
    {
        void Close();
        Stream GetStream();

        // read interface
        int BeginRead();
        int Read(byte[] data, int offset, int len);
        void EndRead();

        // write interface
        void BeginWrite(int seq);
        void Write(byte[] data, int offset, int len);
        void Reset();
        void EndWrite();
        void CancelWrite();
    }

    public abstract class BaseTransport : ITransport
    {
        protected class TransportStream : Stream
        {
            ITransport transport;
            public TransportStream(ITransport transport)
            {
                this.transport = transport;
            }

            public override void Write(byte[] buffer, int offset, int count)
            {
                transport.Write(buffer, offset, count);
            }
            public override int Read(byte[] buffer, int offset, int count)
            {
                return transport.Read(buffer, offset, count);
            }

            public override bool CanRead
            {
                get { return true; }
            }
            public override bool CanSeek
            {
                get { return false; }
            }
            public override bool CanWrite
            {
                get { return true; }
            }
            public override long Length
            {
                get { throw new IOException("not implemented"); }
            }
            public override long Position
            {
                get { throw new IOException("not implemented"); }
                set { throw new IOException("not implemented"); }
            }
            public override void SetLength(long value)
            {
                throw new IOException("not implemented");
            }
            public override long Seek(long offset, SeekOrigin origin)
            {
                throw new IOException("not implemented");
            }
            public override void Flush()
            {
            }
        }

        protected MemoryStream buffer;
        protected Stream inputStream;
        protected Stream outputStream;
        protected Stream asStream;
        protected ReentrantLock rlock;
        protected ReentrantLock wlock;

        protected int wseq;
        protected int rseq;
        protected int rpos;
        protected int rlength;

        public BaseTransport(Stream inputOuputStream) :
            this(inputOuputStream, inputOuputStream, 128 * 1024)
        {
        }

        public BaseTransport(Stream inputStream, Stream outputStream) :
            this(inputStream, outputStream, 128 * 1024)
        {
        }

        public BaseTransport(Stream inputStream, Stream outputStream, int bufsize)
        {
            this.inputStream = inputStream;
            this.outputStream = outputStream;
            buffer = new MemoryStream(bufsize);
            wlock = new ReentrantLock();
            rlock = new ReentrantLock();
            asStream = new TransportStream(this);
        }

        virtual public void Close()
        {
            if (inputStream != null)
            {
                inputStream.Close();
                inputStream = null;
            }
            if (outputStream != null)
            {
                outputStream.Close();
                outputStream = null;
            }
        }

        virtual public Stream GetStream()
        {
            return asStream;
        }

        //
        // read interface
        //
        virtual public int BeginRead()
        {
            lock (this)
            {
                if (rlock.IsHeldByCurrentThread())
                {
                    throw new IOException("beginRead is not reentrant");
                }

                rlock.Acquire();
                rlength = (int)Packers.Int32.unpack(inputStream);
                rseq = (int)Packers.Int32.unpack(inputStream);
                rpos = 0;

                return rseq;
            }
        }

        protected void AssertBeganRead()
        {
            if (!rlock.IsHeldByCurrentThread())
            {
                throw new IOException("thread must first call beginRead");
            }
        }

        virtual public int Read(byte[] data, int offset, int len)
        {
            AssertBeganRead();
            if (rpos + len > rlength)
            {
                throw new EndOfStreamException("request to read more than available");
            }
            int actually_read = inputStream.Read(data, offset, len);
            rpos += actually_read;
            return actually_read;
        }

        virtual public void EndRead()
        {
            lock (this)
            {
                AssertBeganRead();
                byte[] garbage = new byte[16 * 1024];
                int to_skip = rlength - rpos;

                for (int i = 0; i < to_skip; ) {
                    int chunk = to_skip - i;
                    if (chunk > garbage.Length) {
                        chunk = garbage.Length;
                    }
                    inputStream.Read(garbage, 0, chunk);
                }

                rlock.Release();
            }
        }

        //
        // write interface
        //
        virtual public void BeginWrite(int seq)
        {
            lock (this)
            {
                if (wlock.IsHeldByCurrentThread())
                {
                    throw new IOException("beginWrite is not reentrant");
                }
                wlock.Acquire();
                wseq = seq;
                buffer.Position = 0;
                buffer.SetLength(0);
            }
        }

        virtual protected void AssertBeganWrite()
        {
            if (!wlock.IsHeldByCurrentThread())
            {
                throw new IOException("thread must first call beginWrite");
            }
        }

        virtual public void Write(byte[] data, int offset, int len)
        {
            AssertBeganWrite();
            buffer.Write(data, offset, len);
        }

        virtual public void Reset()
        {
            AssertBeganWrite();
            buffer.Position = 0;
            buffer.SetLength(0);
        }

        virtual public void EndWrite()
        {
            lock (this)
            {
                AssertBeganWrite();
                if (buffer.Length > 0)
                {
                    Packers.Int32.pack((int)buffer.Length, outputStream);
                    Packers.Int32.pack(wseq, outputStream);
                    buffer.WriteTo(outputStream);
                    outputStream.Flush();
                    buffer.Position = 0;
                    buffer.SetLength(0);
                }
                wlock.Release();
            }
        }

        virtual public void CancelWrite()
        {
            lock (this)
            {
                AssertBeganWrite();
                buffer.Position = 0;
                buffer.SetLength(0);
                wlock.Release();
            }
        }
    }

    public abstract class WrappedTransport
    {
        protected ITransport transport;

        public WrappedTransport(ITransport transport)
        {
            this.transport = transport;
        }
        public Stream GetStream()
        {
            return transport.GetStream();
        }
        public void Close()
        {
            transport.Close();
        }
        public int BeginRead()
        {
            return transport.BeginRead();
        }
        public int Read(byte[] data, int offset, int len)
        {
            return transport.Read(data, offset, len);
        }
        public void EndRead()
        {
            transport.EndRead();
        }
        public void BeginWrite(int seq)
        {
            transport.BeginWrite(seq);
        }
        public void Write(byte[] data, int offset, int len)
        {
            transport.Write(data, offset, len);
        }
        public void Reset()
        {
            transport.Reset();
        }
        public void EndWrite()
        {
            transport.EndWrite();
        }
        public void CancelWrite()
        {
            transport.EndWrite();
        }
    }

    public class SocketTransport : BaseTransport
    {
        protected Socket sock;
        protected const int bufsize = 16 * 1024;

        public SocketTransport(Socket sock)
            : base(new BufferedStream(new NetworkStream(sock), bufsize))
        {
            this.sock = sock;
        }

        protected static Socket _connect(String host, int port)
        {
            Socket sock = new Socket(AddressFamily.InterNetwork, SocketType.Stream, ProtocolType.Tcp);
            sock.Connect(host, port);
            return sock;
        }

        public SocketTransport(String host, int port)
            : this(_connect(host, port))
        {
        }

        protected static Socket _connect(IPAddress addr, int port)
        {
            Socket sock = new Socket(addr.AddressFamily, SocketType.Stream, ProtocolType.Tcp);
            sock.Connect(addr, port);
            return sock;
        }

        public SocketTransport(IPAddress addr, int port)
            : this(_connect(addr, port))
        {
        }
    }

    public class ProcTransport : WrappedTransport
    {
        public Process proc;

        public ProcTransport(Process proc, ITransport transport)
            : base(transport)
        {
            this.proc = proc;
        }

        public static ProcTransport Connect(string filename)
        {
            return Connect(filename, "-m lib");
        }

        public static ProcTransport Connect(string filename, string args)
        {
            Process proc = new Process();
            proc.StartInfo.UseShellExecute = false;
            proc.StartInfo.FileName = filename;
            proc.StartInfo.Arguments = args;
            proc.StartInfo.CreateNoWindow = true;
            proc.StartInfo.RedirectStandardInput = true;
            proc.StartInfo.RedirectStandardOutput = true;
            proc.StartInfo.RedirectStandardError = true;
            return Connect(proc);
        }

        public static ProcTransport Connect(Process proc)
        {
            proc.Start();
            string hostname = proc.StandardOutput.ReadLine();
            int port = Int16.Parse(proc.StandardOutput.ReadLine());
            ITransport transport = new SocketTransport(hostname, port);
            return new ProcTransport(proc, transport);
        }
    }
}