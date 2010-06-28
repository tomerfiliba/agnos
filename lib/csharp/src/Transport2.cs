using System;
using System.IO;
using System.Net;
using System.Net.Sockets;
using System.Diagnostics;


namespace Agnos.Transport2
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

	protected static class TransportStream : Stream
	{
		ITransport transport;
		public TransportStream(ITransport transport)
		{
			this.transport = transport;
		}
		
		public void Write(byte[] buffer, int offset, int count)
		{
			transport.Write(data, off, len);
		}
		public int Read(	byte[] buffer, int offset, int count)
		{
			return transport.Read(buffer, offset, count);
		}
		
		public override bool CanRead {
			get{return true;}
		}
		public override bool CanSeek {
			get{return false;}
		}
		public override bool CanWrite {
			get{return true;}
		}
		public override long Length {
			get{throw new IOException("not implemented");}
		}
		public override long Position {
			get{throw new IOException("not implemented");}
		}
		public override long SetLength(long value) {
			throw new IOException("not implemented");
		}
		public override long Seek(long offset, SeekOrigin origin) {
			throw new IOException("not implemented");
		}
		public override void Flush()
		{
		}
	}

	public abstract class BaseTransport : ITransport
	{
		protected MemoryStream buffer;
		protected Stream underlyingStream;
		protected Stream asStream;

		protected int wseq;
		protected int rseq;
		protected int rpos;
		protected int rlength;

		public BaseTransport(Stream underlyingStream)
		{
			this(underlyingStream, 128 * 1024);
		}

		public BaseTransport(Stream underlyingStream, int bufsize)
		{
			this.underlyingStream = underlyingStream;
			buffer = new MemoryStream(bufsize);
			//wlock = new ReentrantLock();
			//rlock = new ReentrantLock();
			asStream = new TransportStream(this);
		}
		
		public void Close()
		{
			if (underlyingStream != null) {
				underlyingStream.Close();
			}
		}

		public Stream GetStream()
		{
			return asStream;
		}

		//
		// read interface
		//
		public int BeginRead()
		{
			lock(this) {
				if (rlock.isHeldByCurrentThread()) {
					throw new IOException("beginRead is not reentrant");
				}
				
				//rlock.lock();
				rlength = (Integer)Packers.Int32.unpack(input);
				rseq = (Integer)Packers.Int32.unpack(input);
				rpos = 0;
				
				return rseq;
			}
		}

		protected void AssertBeganRead()
		{
			if (!rlock.isHeldByCurrentThread()) {
				throw new IOException("thread must first call beginRead");
			}
		}
		
		public int Read(byte[] data, int offset, int len)
		{
			AssertBeganRead();
			if (rpos + len > rlength) {
				throw new EOFException("request to read more than available");
			}
			int actually_read = underlyingStream.read(data, offset, len);
			rpos += actually_read;
			return actually_read;
		}
		
		public void EndRead() throws IOException
		{
			lock(this) {
				AssertBeganRead();
				underlyingStream.skip(rlength - rpos);
				rlock.unlock();
			}
		}
		
		//
		// write interface
		//
		public void BeginWrite(int seq)
		{
			lock(this) {
				if (wlock.isHeldByCurrentThread()) {
					throw new IOException("beginWrite is not reentrant");
				}
				wlock.lock();
				wseq = seq;
				buffer.reset();
			}
		}
		
		protected void AssertBeganWrite() throws IOException
		{
			if (!wlock.isHeldByCurrentThread()) {
				throw new IOException("thread must first call beginWrite");
			}
		}

		public void Write(byte[] data, int offset, int len) throws IOException
		{
			assertBeganWrite();
			buffer.write(data, offset, len);
		}
		
		public void Reset() throws IOException
		{
			AssertBeganWrite();
			buffer.Position = 0;
			buffer.SetLength(0);
		}

		public void EndWrite()
		{
			lock(this) {
				AssertBeganWrite();
				if (buffer.size() > 0) {
					Packers.Int32.pack(buffer.size(), underlyingStream);
					Packers.Int32.pack(wseq, underlyingStream);
					//buffer.writeTo(output);
					underlyingStream.Flush();
					buffer.Position = 0;
					buffer.SetLength(0);
				}
				wlock.unlock();
			}
		}

		public void CancelWrite()
		{
			lock(this) {
				assertBeganWrite();
				buffer.reset();
				wlock.unlock();
			}
		}
	}

	public static abstract class WrappedTransport
	{
		protected ITransport transport;
		
		public WrappedTransport(ITransport transport) {
			this.transport = transport;
		}
		public Stream GetStream() {
			return transport.GetStream();
		}
		public void Close() {
			transport.close();
		}
		public int BeginRead() {
			return transport.beginRead();
		}
		public int Read(byte[] data, int offset, int len) {
			return transport.read(data, offset, len);
		}
		public void EndRead() {
			transport.endRead();
		}
		public void BeginWrite(int seq) {
			transport.beginWrite(seq);
		}
		public void Write(byte[] data, int offset, int len) {
			transport.write(data, offset, len);
		}
		public void Reset() {
			transport.reset();
		}
		public void EndWrite() {
			transport.endWrite();
		}
		public void CancelWrite() {
			transport.endWrite();
		}
	}
}

