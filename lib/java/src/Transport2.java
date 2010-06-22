package agnos;

import java.io.*;
import java.util.*;
import java.util.concurrent.locks.*;


public class Transport2
{
	public static class SimpleTransport
	{
		protected ByteArrayOutputStream buffer;
		protected InputStream input
		protected OutputStream output;
		protected ReentrantLock rlock;
		protected ReentrantLock wlock;

		protected int wseq;
		protected int rseq;
		protected int rpos;
		protected int rlength;

		public SimpleTransport(InputStream input, OutputStream output)
		{
			this.input = input;
			this.output = output;
			buffer = new ByteArrayOutputStream(128 * 1024);
			wseq = 0;
			wlock = new ReentrantLock();
			rlock = new ReentrantLock();
		}
		
		//
		// read
		//
		
		public synchronized int beginRead()
		{
			if (this.wlock.isHeldByCurrentThread()) {
				throw new IOException("cannot recursively call beginRead");
			}
			
			this.rlock.lock();
			rlength = (Integer)Packers.Int32.unpack(input);
			rseq = (Integer)Packers.Int32.unpack(input);
			rpos = 0;
			
			return rseq;
		}
		
		public int read(byte[] data, int offset, int size)
		{
			if (!this.rlock.isHeldByCurrentThread()) {
				throw new IOException("thread must first call beginRead");
			}
			if (position + size > length) {
				throw new EOFException("request to read more than available");
			}
			int actually_read = input.read(data, offset, size);
			rpos += actually_read;
			return actually_read;
		}
		
		public synchronized void endRead()
		{
			if (!this.rlock.isHeldByCurrentThread()) {
				throw new IOException("thread must first call beginRead");
			}
			
			this.lock.unlock();
		}
		
		//
		// write
		//
		
		public synchronized int beginWrite()
		{
			if (this.wlock.isHeldByCurrentThread()) {
				throw new IOException("cannot recursively call beginWrite");
			}
			this.wlock.lock();
			seq += 1;
			buffer.reset();
			return seq;
		}
		
		public void write(byte[] data, int offset, int size)
		{
			if (!this.wlock.isHeldByCurrentThread()) {
				throw new IOException("thread must first call beginWrite");
			}
			buffer.write(data, offset, size);
		}
		
		public void reset()
		{
			if (!this.wlock.isHeldByCurrentThread()) {
				throw new IOException("thread must first call beginWrite");
			}
			buffer.reset();
		}

		public synchronized void endWrite()
		{
			if (!this.wlock.isHeldByCurrentThread()) {
				throw new IOException("thread must first call beginWrite");
			}
			if (buffer.size() > 0) {
				Packers.Int32.pack(buffer.size(), output);
				Packers.Int32.pack(seq, output);
				buffer.writeTo(output);
				buffer.flush();
				buffer.reset();
			}
			this.wlock.unlock();
		}
	}
	
	
	
	
}


















