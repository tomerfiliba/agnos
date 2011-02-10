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

	public interface ITransport : IDisposable
	{
		void Close ();
		Stream GetInputStream ();
		Stream GetOutputStream ();

		bool IsCompressionEnabled ();
		bool EnableCompression ();
		void DisableCompression ();

		// read interface
		int BeginRead ();
		int Read (byte[] data, int offset, int len);
		void EndRead ();

		// write interface
		void BeginWrite (int seq);
		void Write (byte[] data, int offset, int len);
		void RestartWrite ();
		void EndWrite ();
		void CancelWrite ();
	}

	internal sealed class TransportStream : Stream
	{
		readonly private ITransport transport;
		readonly private bool output;
		
		public TransportStream (ITransport transport, bool output)
		{
			this.transport = transport;
			this.output = output;
		}

		public override void Close ()
		{
			if (output) {
				transport.EndWrite();
			}
			else {
				transport.EndRead();
			}
		}

		public override void Write (byte[] buffer, int offset, int count)
		{
			if (!output) {
				throw new InvalidOperationException("this stream is opened for reading only");
			}
			transport.Write (buffer, offset, count);
		}
		public override int Read (byte[] buffer, int offset, int count)
		{
			if (output) {
				throw new InvalidOperationException("this stream is opened for writing only");
			}
			return transport.Read (buffer, offset, count);
		}

		public override bool CanRead {
			get { return !output; }
		}
		public override bool CanSeek {
			get { return false; }
		}
		public override bool CanWrite {
			get { return output; }
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


	public abstract class BaseTransport : ITransport
	{
		protected const int INITIAL_BUFFER_SIZE = 128 * 1024;

		protected Stream inStream;
		protected Stream outStream;

		protected readonly MemoryStream wbuffer = new MemoryStream (INITIAL_BUFFER_SIZE);
		protected readonly MemoryStream compressionBuffer = new MemoryStream (INITIAL_BUFFER_SIZE);
		private readonly TransportStream asInputStream;
		private readonly TransportStream asOutputStream;
		protected readonly ReentrantLock rlock = new ReentrantLock ();
		protected readonly ReentrantLock wlock = new ReentrantLock ();

		protected BoundInputStream readStream;
		protected int wseq = 0;
		protected int compressionThreshold = -1;

		public BaseTransport (Stream inOutStream) : this(inOutStream, inOutStream)
		{
		}

		public BaseTransport (Stream inStream, Stream outStream)
		{
			this.inStream = inStream;
			this.outStream = outStream;
			asInputStream = new TransportStream (this, false);
			asOutputStream = new TransportStream (this, true);
		}

		public void Dispose ()
		{
			Close();
		}

		public virtual void Close ()
		{
			if (inStream != null) {
				inStream.Close ();
				inStream = null;
			}
			if (outStream != null) {
				outStream.Close ();
				outStream = null;
			}
		}

		public virtual Stream GetInputStream ()
		{
			return asInputStream;
		}
		public virtual Stream GetOutputStream ()
		{
			return asOutputStream;
		}
		public virtual bool IsCompressionEnabled ()
		{
			return compressionThreshold > 0;
		}
		public virtual bool EnableCompression ()
		{
			compressionThreshold = getCompressionThreshold ();
			return compressionThreshold > 0;
		}
		public virtual void DisableCompression ()
		{
			compressionThreshold = -1;
		}

		protected virtual int getCompressionThreshold ()
		{
			return -1;
		}

		protected static int readSInt32(Stream stream) 
		{
			byte[] buf = new byte[4];
			int len = stream.Read(buf, 0, buf.Length);
			if (len < buf.Length) {
				throw new EndOfStreamException("expected " + buf.Length + " bytes, got " + len);
			}
			return ((int)(buf[0] & 0xff) << 24) | 
					((int)(buf[1] & 0xff) << 16) | 
					((int)(buf[2] & 0xff) << 8) | 
					((int)(buf[3] & 0xff));
		}

		protected static void writeSInt32(Stream stream, int val) 
		{
			byte[] buf = {(byte)((val >> 24) & 0xff),
				(byte)((val >> 16) & 0xff),
				(byte)((val >> 8) & 0xff),
				(byte)((val) & 0xff)};
			stream.Write(buf, 0, buf.Length);
		}

		//
		// read interface
		//
		public virtual int BeginRead ()
		{
			if (rlock.IsHeldByCurrentThread ()) {
				throw new IOException ("beginRead is not reentrant");
			}
			
			rlock.Acquire ();
			try {
				int seq = readSInt32(inStream);
				int packetLength = readSInt32(inStream);
				int uncompressedLength = readSInt32(inStream);
				
				if (readStream != null) {
					throw new InvalidOperationException ("readStream must be null at this point");
				}
				
				readStream = new BoundInputStream (inStream, packetLength, true, false);
				if (uncompressedLength > 0) {
					readStream = new BoundInputStream (new DeflateStream (readStream, CompressionMode.Decompress, false), packetLength, false, true);
				}
				return seq;
			} catch (Exception) {
				readStream = null;
				rlock.Release ();
				throw;
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
			if (len > readStream.Available) {
				throw new EndOfStreamException ("request to read more than available");
			}
			return readStream.Read (data, offset, len);
		}

		public virtual void EndRead ()
		{
			AssertBeganRead ();
			readStream.Close ();
			readStream = null;
			rlock.Release ();
		}

		//
		// write interface
		//
		public virtual void BeginWrite (int seq)
		{
			if (wlock.IsHeldByCurrentThread ()) {
				throw new IOException ("beginWrite is not reentrant");
			}
			wlock.Acquire ();
			wseq = seq;
			wbuffer.Position = 0;
			wbuffer.SetLength (0);
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
			wbuffer.Write (data, offset, len);
		}

		public virtual void RestartWrite ()
		{
			AssertBeganWrite ();
			wbuffer.Position = 0;
			wbuffer.SetLength (0);
		}

		public virtual void EndWrite ()
		{
			AssertBeganWrite ();
			if (wbuffer.Length > 0) {
				writeSInt32(outStream, wseq);
				
				if (compressionThreshold > 0 && wbuffer.Length >= compressionThreshold) {
					compressionBuffer.Position = 0;
					compressionBuffer.SetLength (0);
					using (DeflateStream dfl = new DeflateStream (compressionBuffer, CompressionMode.Compress, true)) {
						wbuffer.WriteTo (dfl);
					}
					writeSInt32 (outStream, (int)compressionBuffer.Length); // packet length
					writeSInt32 (outStream, (int)wbuffer.Length); // uncompressed length
					compressionBuffer.WriteTo (outStream);
				} 
				else {
					writeSInt32 (outStream, (int)wbuffer.Length); // packet length
					writeSInt32 (outStream, 0); // 0 means no compression
					wbuffer.WriteTo (outStream);
				}
				
				outStream.Flush ();
			}
			
			wbuffer.Position = 0;
			wbuffer.SetLength (0);
			wlock.Release ();
		}

		public virtual void CancelWrite ()
		{
			AssertBeganWrite ();
			wbuffer.Position = 0;
			wbuffer.SetLength (0);
			wlock.Release ();
		}
	}

	public abstract class WrappedTransport : ITransport
	{
		protected ITransport transport;

		public WrappedTransport (ITransport transport)
		{
			this.transport = transport;
		}
		public Stream GetInputStream ()
		{
			return transport.GetInputStream ();
		}
		public Stream GetOutputStream ()
		{
			return transport.GetOutputStream ();
		}
		public bool IsCompressionEnabled ()
		{
			return this.IsCompressionEnabled ();
		}
		public bool EnableCompression ()
		{
			return transport.EnableCompression ();
		}
		public void DisableCompression ()
		{
			transport.DisableCompression ();
		}
		public void Dispose ()
		{
			Close();
		}
		public void Close ()
		{
			transport.Close ();
		}
		public int BeginRead ()
		{
			return transport.BeginRead ();
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
		public void RestartWrite ()
		{
			transport.RestartWrite ();
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

		public SocketTransport (Socket sock) : base(new BufferedStream (new NetworkStream (sock, true), DEFAULT_BUFSIZE))
		{
			this.sock = sock;
		}

		static internal Socket _connect (String host, int port)
		{
			Socket sock = new Socket (AddressFamily.InterNetwork, SocketType.Stream, ProtocolType.Tcp);
			sock.Connect (host, port);
			return sock;
		}

		public SocketTransport (String host, int port) : this(_connect (host, port))
		{
		}

		static internal Socket _connect (IPAddress addr, int port)
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

		public SslSocketTransport (SslStream stream) : this(stream, SocketTransport.DEFAULT_BUFSIZE)
		{
		}

		public SslSocketTransport (SslStream stream, int bufsize) : base(new BufferedStream (stream, bufsize))
		{
			this.sock = null;
		}

		public SslSocketTransport (String host, int port) : this(SocketTransport._connect (host, port))
		{
		}

		public SslSocketTransport (IPAddress addr, int port) : this(SocketTransport._connect (addr, port))
		{
		}

		public SslSocketTransport (Socket sock) : base(new BufferedStream (new SslStream (new NetworkStream (sock, true), false), SocketTransport.DEFAULT_BUFSIZE))
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
