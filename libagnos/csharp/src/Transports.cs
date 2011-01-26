//////////////////////////////////////////////////////////////////////////////
// Part of the Agnos RPC Framework
//    http://agnos.sourceforge.net
//
// Copyright 2011, International Business Machines Corp.
//                 Author: Tomer Filiba (tomerf@il.ibm.com)
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//    http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.
//////////////////////////////////////////////////////////////////////////////

using System;
using System.IO;
using System.IO.Compression;
using System.Net;
using System.Net.Sockets;
using System.Net.Security;
using System.Security.Authentication;
using System.Security.Cryptography.X509Certificates;
using System.Diagnostics;
using Agnos.Utils;


namespace Agnos.Transports
{
	public class TransportException : IOException
	{
		public TransportException (String message) : base(message)
		{
		}
	}

	public interface ITransport
	{
		void Close ();
		Stream GetStream ();
		int GetCompressionThreshold();
		void SetCompressionThreshold(int value);
		void DisableCompression();

		// read interface
		int BeginRead ();
		int BeginRead (int msecs);
		int Read (byte[] data, int offset, int len);
		void EndRead ();

		// write interface
		void BeginWrite (int seq);
		void Write (byte[] data, int offset, int len);
		void Reset ();
		void EndWrite ();
		void CancelWrite ();
	}

	public abstract class BaseTransport : ITransport
	{
		protected sealed class TransportStream : Stream
		{
			readonly ITransport transport;
			public TransportStream (ITransport transport)
			{
				this.transport = transport;
			}

			public override void Write (byte[] buffer, int offset, int count)
			{
				transport.Write (buffer, offset, count);
			}
			public override int Read (byte[] buffer, int offset, int count)
			{
				return transport.Read (buffer, offset, count);
			}

			public override bool CanRead {
				get { return true; }
			}
			public override bool CanSeek {
				get { return false; }
			}
			public override bool CanWrite {
				get { return true; }
			}
			public override long Length {
				get {
					throw new IOException ("not implemented");
				}
			}
			public override long Position {
				get {
					throw new IOException ("not implemented");
				}
				set {
					throw new IOException ("not implemented");
				}
			}
			public override void SetLength (long value)
			{
				throw new IOException ("not implemented");
			}
			public override long Seek (long offset, SeekOrigin origin)
			{
				throw new IOException ("not implemented");
			}
			public override void Flush ()
			{
			}
		}

		protected MemoryStream buffer;
		protected MemoryStream compBuffer;
		protected Stream inputStream;
		protected Stream inputStream2;
		protected Stream outputStream;
		protected Stream asStream;
		protected ReentrantLock rlock;
		protected ReentrantLock wlock;

		protected int wseq;
		protected int rseq;
		protected int rpos;
		protected int rlength;
		protected int rcomplength;
		protected int compressionThreshold;

		public int GetCompressionThreshold()
		{
			return compressionThreshold;
		}
		
		public void SetCompressionThreshold(int value)
		{
			compressionThreshold = value;
		}
		
		public void DisableCompression() 
		{
			compressionThreshold = -1;
		}

		public BaseTransport (Stream inputOuputStream) : 
			this(inputOuputStream, inputOuputStream, 128 * 1024)
		{
		}

		public BaseTransport (Stream inputStream, Stream outputStream) : 
			this(inputStream, outputStream, 128 * 1024)
		{
		}

		public BaseTransport (Stream inputStream, Stream outputStream, int bufsize)
		{
			this.inputStream = inputStream;
			this.outputStream = outputStream;
			this.compressionThreshold = -1;
			inputStream2 = null;
			buffer = new MemoryStream (bufsize);
			compBuffer = new MemoryStream (bufsize);
			wlock = new ReentrantLock ();
			rlock = new ReentrantLock ();
			asStream = new TransportStream (this);
		}

		public virtual void Close ()
		{
			if (inputStream != null) {
				inputStream.Close ();
				inputStream = null;
				inputStream2 = null;
			}
			if (outputStream != null) {
				outputStream.Close ();
				outputStream = null;
			}
		}

		public virtual Stream GetStream ()
		{
			return asStream;
		}

		//
		// read interface
		//
		public virtual int BeginRead ()
		{
			return BeginRead (-1);
		}

		public virtual int BeginRead (int msecs)
		{
			lock (this) {
				if (rlock.IsHeldByCurrentThread ()) {
					throw new IOException ("beginRead is not reentrant");
				}
				
				rlock.Acquire ();
				rseq = (int)Packers.Int32.unpack (inputStream);
				rlength = (int)Packers.Int32.unpack (inputStream);
				rcomplength = (int)Packers.Int32.unpack (inputStream);
				rpos = 0;
				
				if (rcomplength > 0) {
					throw new NotImplementedException();

					/*int tmp = rlength;
					rlength = rcomplength;
					rcomplength = tmp;
					inputStream2 = new DeflateStream(inputStream, CompressionMode.Decompress, true);
					*/
				}
				/*else {
					inputStream2 = inputStream;
				}*/
				
				return rseq;
			}
		}

		protected void AssertBeganRead ()
		{
			if (!rlock.IsHeldByCurrentThread ()) {
				throw new IOException ("thread must first call beginRead");
			}
		}

		public virtual int Read (byte[] data, int offset, int len)
		{
			AssertBeganRead ();
			if (rpos + len > rlength) {
				throw new EndOfStreamException ("request to read more than available");
			}
			int actually_read = inputStream.Read (data, offset, len);
			rpos += actually_read;
			return actually_read;
		}

		public virtual void EndRead ()
		{
			lock (this) {
				AssertBeganRead ();
				byte[] garbage = new byte[16 * 1024];
				int to_skip = rlength - rpos;
				
				for (int i = 0; i < to_skip;) {
					int chunk = to_skip - i;
					if (chunk > garbage.Length) {
						chunk = garbage.Length;
					}
					i += inputStream.Read (garbage, 0, chunk);
				}
				
				rlock.Release ();
			}
		}

		//
		// write interface
		//
		public virtual void BeginWrite (int seq)
		{
			lock (this) {
				if (wlock.IsHeldByCurrentThread ()) {
					throw new IOException ("beginWrite is not reentrant");
				}
				wlock.Acquire ();
				wseq = seq;
				buffer.Position = 0;
				buffer.SetLength (0);
			}
		}

		protected virtual void AssertBeganWrite ()
		{
			if (!wlock.IsHeldByCurrentThread ()) {
				throw new IOException ("thread must first call beginWrite");
			}
		}

		public virtual void Write (byte[] data, int offset, int len)
		{
			AssertBeganWrite ();
			buffer.Write (data, offset, len);
		}

		public virtual void Reset ()
		{
			AssertBeganWrite ();
			buffer.Position = 0;
			buffer.SetLength (0);
		}

		public virtual void EndWrite ()
		{
			lock (this) {
				AssertBeganWrite ();
				if (buffer.Length > 0) {
					Packers.Int32.pack (wseq, outputStream);
					
					if (compressionThreshold >= 0 && buffer.Length >= compressionThreshold) {
						throw new NotImplementedException();
					
						/*compBuffer.Position = 0;
						compBuffer.SetLength(0);
						using (DeflateStream dfl = new DeflateStream(compBuffer, CompressionMode.Compress, true)) {
							buffer.WriteTo(dfl);
						}
						Packers.Int32.pack (compBuffer.Length, outputStream); // actual size
						Packers.Int32.pack (buffer.Length, outputStream); // uncompressed size

						compBuffer.WriteTo(outputStream);
						
						buffer.Position = 0;
						buffer.SetLength (0);
						compBuffer.Position = 0;
						compBuffer.SetLength(0);*/
					}
					else {
						Packers.Int32.pack ((int)buffer.Length, outputStream); // actual size
						Packers.Int32.pack (0, outputStream); // 0 means no compression
						
						buffer.WriteTo (outputStream);
						buffer.Position = 0;
						buffer.SetLength (0);
					}
					
					outputStream.Flush ();
				}
				wlock.Release ();
			}
		}

		public virtual void CancelWrite ()
		{
			lock (this) {
				AssertBeganWrite ();
				buffer.Position = 0;
				buffer.SetLength (0);
				wlock.Release ();
			}
		}
	}

	public abstract class WrappedTransport : ITransport
	{
		protected ITransport transport;

		public WrappedTransport (ITransport transport)
		{
			this.transport = transport;
		}
		public Stream GetStream ()
		{
			return transport.GetStream ();
		}
		public int GetCompressionThreshold()
		{
			return this.GetCompressionThreshold();
		}
		public void SetCompressionThreshold(int value)
		{
			transport.SetCompressionThreshold(value);
		}
		public void DisableCompression() 
		{
			transport.DisableCompression();
		}		
		public void Close ()
		{
			transport.Close ();
		}
		public int BeginRead ()
		{
			return transport.BeginRead ();
		}
		public int BeginRead (int msecs)
		{
			return transport.BeginRead (msecs);
		}
		public int Read (byte[] data, int offset, int len)
		{
			return transport.Read (data, offset, len);
		}
		public void EndRead ()
		{
			transport.EndRead ();
		}
		public void BeginWrite (int seq)
		{
			transport.BeginWrite (seq);
		}
		public void Write (byte[] data, int offset, int len)
		{
			transport.Write (data, offset, len);
		}
		public void Reset ()
		{
			transport.Reset ();
		}
		public void EndWrite ()
		{
			transport.EndWrite ();
		}
		public void CancelWrite ()
		{
			transport.EndWrite ();
		}
	}

	public class SocketTransport : BaseTransport
	{
		protected readonly Socket sock;
		public const int DEFAULT_BUFSIZE = 16 * 1024;
		public const int DEFAULT_COMPRESSION_THRESHOLD = 4 * 1024;

		public SocketTransport (Socket sock) : 
			base(new BufferedStream (new NetworkStream (sock, true), DEFAULT_BUFSIZE))
		{
			this.sock = sock;
		}

		internal static Socket _connect (String host, int port)
		{
			Socket sock = new Socket (AddressFamily.InterNetwork, SocketType.Stream, ProtocolType.Tcp);
			sock.Connect (host, port);
			return sock;
		}

		public SocketTransport (String host, int port) : this(_connect (host, port))
		{
		}

		internal static Socket _connect (IPAddress addr, int port)
		{
			Socket sock = new Socket (addr.AddressFamily, SocketType.Stream, ProtocolType.Tcp);
			sock.Connect (addr, port);
			return sock;
		}

		public SocketTransport (IPAddress addr, int port) : this(_connect (addr, port))
		{
		}
	}

	public class SslSocketTransport : BaseTransport
	{
		public const int DEFAULT_COMPRESSION_THRESHOLD = 4 * 1024;
		protected readonly Socket sock;

		public SslSocketTransport(SslStream stream) : 
			this(stream, SocketTransport.DEFAULT_BUFSIZE)
		{
		}

		public SslSocketTransport(SslStream stream, int bufsize) : 
			base(new BufferedStream(stream, bufsize))
		{
			this.sock = null;
		}

		public SslSocketTransport(String host, int port) : 
			this(SocketTransport._connect(host, port))
		{
		}

		public SslSocketTransport(IPAddress addr, int port) : 
			this(SocketTransport._connect(addr, port))
		{
		}

		public SslSocketTransport(Socket sock) : 
			base(new BufferedStream(new SslStream(new NetworkStream(sock, true), false), 
					SocketTransport.DEFAULT_BUFSIZE))
		{
			this.sock = sock;
		}
	}

	public class ProcTransport : WrappedTransport
	{
		public readonly Process proc;

		public ProcTransport (Process proc, ITransport transport) : base(transport)
		{
			this.proc = proc;
		}

		public static ProcTransport Connect (string filename)
		{
			return Connect (filename, "-m lib");
		}

		public static ProcTransport Connect (string filename, string args)
		{
			Process proc = new Process ();
			proc.StartInfo.UseShellExecute = false;
			proc.StartInfo.FileName = filename;
			proc.StartInfo.Arguments = args;
			proc.StartInfo.CreateNoWindow = true;
			proc.StartInfo.RedirectStandardInput = true;
			proc.StartInfo.RedirectStandardOutput = true;
			proc.StartInfo.RedirectStandardError = true;
			return Connect (proc);
		}

		public static ProcTransport Connect (Process proc)
		{
			proc.Start ();
			if (proc.StandardOutput.ReadLine () != "AGNOS") {
				throw new TransportException ("process " + proc + " did not start correctly");
			}
			string hostname = proc.StandardOutput.ReadLine ();
			int port = Int16.Parse (proc.StandardOutput.ReadLine ());
			ITransport transport = new SocketTransport (hostname, port);
			return new ProcTransport (proc, transport);
		}
	}
}
