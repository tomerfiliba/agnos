import java.io.InputStream;
import java.io.OutputStream;

public interface ITransport
{
	public void enableCompression(int threshold);
	public void disableCompression();
	public int getCompressionThreshold();
	
	public IReadTransaction beginRead() throws IOException;
	public IWriteTransaction beginWrite() throws IOException;
}

public interface IReadTransaction
{
	public int getSeq();
	public int read(byte[] output, int offset, int length) throws IOException;
	public void end() throws IOException;
}

public interface IWriteTransaction
{
	public int write(byte[] output, int offset, int length) throws IOException;
	public void reset();
	public void end() throws IOException;
}

class BoundInputStream extends InputStream
{
	protected InputStream inputStream;
	protected int length;
	protected int consumedLength;
	
	public BoundInputStream(InputStream inputStream, int length) {
		this.inputStream = inputStream;
		this.length = length;
		this.consumedLength = 0;
	}

	@Override
	public int available() throws IOException {
		return length - consumedLength;
	}
	
	@Override
	public void close() throws IOException {
		if (inputStream == null) {
			return;
		}
		skip(-1);
		inputStream = null;
	}
	
	@Override
	public public int read() throws IOException {
		byte[] buf = {0};
		if (read(arr, 0, arr.length) < 0) {
			return -1;
		}
		return arr[0];
	}

	@Override
	public int read(byte[] buf, int off, int len) throws IOException {
		if (len > length - consumedLength) {
			throw new EOFException("request to read more than available");
		}
		int n = inputStream.read(buf, off, len);
		consumedLength += n;
		return n;
	}
	
	@Override
	public long skip(long n) throws IOException {
		if (n < 0 || n > length - consumedLength) {
			n = length - consumedLength;
		}
		if (n <= 0) {
			return 0;
		}
		n = inputStream.skip(n);
		consumedLength += n;
		return n;
	}
    
}

import java.util.concurrent.locks.ReentrantLock;
import java.util.zip.DeflaterOutputStream;


class BaseTransport implements ITransport
{
	protected int compressionThreshold;
	protected final ReentrantLock rlock;
	protected final ReentrantLock wlock;
	protected IReadTransaction rtrans;
	protected IWriteTransaction wtrans;
	protected final ByteArrayOutputStream wbuffer;
	
	protected static final int INITIAL_BUFFER_SIZE = 128 * 1024;
	
	public BaseTransport() {
		compressionThreshold = -1;
		wlock = new ReentrantLock();
		rlock = new ReentrantLock();
		rtrans = null;
		wtrans = null;
		wbuffer = new ByteArrayOutputStream(INITIAL_BUFFER_SIZE);
	}
	
	public void enableCompression(int threshold) {
		compressionThreshold = threshold;		
	}
	public void disableCompression() {
		compressionThreshold = -1;
	}
	public int getCompressionThreshold() {
		return compressionThreshold;
	}
	
	private void assertBeganRead(IReadTransaction trans) {
		if (!rlock.isHeldByCurrentThread()) {
			throw new IOException("thread must first call beginRead");
		}
		if (trans != rtrans) {
			throw new IOException("invalid transaction");
		}
	}
	
	private void endReadTransaction()
	{
		rtrans = null;
		rlock.unlock();
	}
	
	protected class ReadTransaction implements IReadTransaction {
		private BoundInputStream bis;
		private int seq;
		
		public ReadTransaction(int seq, BoundInputStream bis) {
			this.bis = bis;
			this.seq = seq;
		}
		public int getSeq() {
			return seq;
		}
		public int read(byte[] buf, int off, int len) throws IOException {
			assertBeganRead(this);
			return bis.read(buf, off, len);
		}
		public void end() throws IOException {
			assertBeganRead(this);
			bis.close();
			endReadTransaction();
		}
	}

	protected class WriteTransaction implements IWriteTransaction {
		protected OutputStream outputStream;
		protected int seq;
		
		public WriteTransaction(int seq, OutputStream outputStream) {
			this.seq = seq;
			this.outputStream = outputStream;
			wbuffer.reset();
		}
		public int write(byte[] buf, int off, int len) throws IOException {
			assertBeganWrite(this);
			wbuffer.write(buf, off, len);
		}
		public void reset() {
			assertBeganWrite(this);
			wbuffer.reset();
		}
		public void end() throws IOException {
			assertBeganWrite(this);
			if (wbuffer.length() > 0) {
				Builtin.Int32.pack(seq, output);
				Builtin.Int32.pack(wbuffer.length(), output); // actual size
				Builtin.Int32.pack(-1, output); // -1 means no compression
				wbuffer.writeTo(outputStream);
				outputStream.flush();
			}
			endWriteTransaction();
		}
	}	
	
	public IReadTransaction beginRead() {
		if (rlock.isHeldByCurrentThread()) {
			throw new IOException("beginRead is not reentrant");
		}

		rlock.lock();
		int seq = (Integer) Builtin.Int32.unpack(input);
		int packetLength = (Integer) Builtin.Int32.unpack(input);
		int uncompressedLength = (Integer) Builtin.Int32.unpack(input);
		
		BoundInputStream bis = new BoundInputStream(inputStream, packetLength);
		
		if (uncompressedLength >= 0) {
			bis2 = new BoundInputStream(new InflaterInputStream(bis), 
					uncompressedLength);
		}
		rtrans = new ReadTransaction(seq, bis);
		return rtrans;
	}
	
	public IWriteTransaction beginWrite() {
		
	}

}










































