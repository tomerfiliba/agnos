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

package agnos.transports;

import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.io.OutputStream;
import java.io.EOFException;
import java.io.IOException;
import java.util.concurrent.locks.ReentrantLock;
import java.util.zip.DeflaterOutputStream;
import java.util.zip.InflaterInputStream;
import java.util.logging.Logger;
import java.util.logging.Level;

import agnos.packers.Builtin;
import agnos.util.ClosedOutputStream;
import agnos.util.ClosedInputStream;
import agnos.util.BoundedInputStream;
import agnos.util.DebugStreams;
import agnos.util.SimpleLogger;


/**
 * The base transport class -- implements the common logic used by most (if not all)
 * derived transports. See {@agnos.transports.ITransport ITransport} for documentation.
 * 
 * @author Tomer Filiba
 *
 */
public abstract class BaseTransport implements ITransport {
	protected final static int INITIAL_BUFFER_CAPACITY = 128 * 1024; 
		
	protected InputStream inStream;
	protected OutputStream outStream;
	protected final ReentrantLock rlock = new ReentrantLock();
	//protected final ReentrantLock wlock = rlock;
	protected final ReentrantLock wlock = new ReentrantLock();
	
	private BoundedInputStream readStream = null;
	
	private int compressionThreshold = -1;
	private int wseq = 0;
	
	private final ByteArrayOutputStream wbuffer = 
		new ByteArrayOutputStream(INITIAL_BUFFER_CAPACITY);
	private final ByteArrayOutputStream compressionBuffer = 
		new ByteArrayOutputStream(INITIAL_BUFFER_CAPACITY);
	
	private final InputStream asInputStream = new InputStream() {
		@Override
		public int read() throws IOException
		{
			byte[] buffer = { 0 };
			if (read(buffer) < 0) {
				return -1;
			}
			return buffer[0];
		}
		@Override 
		public int read(byte[] data) throws IOException
		{
			return BaseTransport.this.read(data, 0, data.length);
		}
		@Override 
		public int read(byte[] data, int off, int len) throws IOException
		{
			return BaseTransport.this.read(data, off, len);
		}
		@Override
		public void close() throws IOException
		{
			endRead();
		}
	};
	
	private final OutputStream asOutputStream = new OutputStream() {
		@Override 
		public void write(int b) throws IOException
		{
			write(new byte[] {(byte) b});
		}
		@Override 
		public void write(byte[] data) throws IOException
		{
			BaseTransport.this.write(data, 0, data.length);
		}
		@Override 
		public void write(byte[] data, int off, int len) throws IOException
		{
			BaseTransport.this.write(data, off, len);
		}
		@Override
		public void close() throws IOException
		{
			endWrite();
		}
	};
	
	private Logger logger = SimpleLogger.getLogger("TRNS");
	
	public BaseTransport(InputStream inStream, OutputStream outStream) {
		/*this.inStream = new DebugStreams.LoggingInputStream(logger, inStream);
		this.outStream = new DebugStreams.LoggingOutputStream(logger, outStream);*/
		this.inStream = inStream;
		this.outStream = outStream;
	}
	
	@Override
	public void close() throws IOException {
		logger.info("close()");
		if (readStream != null) {
			readStream.close();
		}
		inStream.close();
		inStream = ClosedInputStream.getInstance();
		outStream.close();
		outStream = ClosedOutputStream.getInstance();
	}
	
	@Override
	public InputStream getInputStream()
	{
		return asInputStream;
	}

	@Override
	public OutputStream getOutputStream()
	{
		return asOutputStream;
	}
	
	@Override
	public boolean enableCompression() {
		compressionThreshold = getCompressionThreshold();
		return compressionThreshold > 0;
	}
	
	protected abstract int getCompressionThreshold();
	
	@Override
	public void disableCompression() {
		compressionThreshold = -1;
	}
	
	@Override
	public boolean isCompressionEnabled() {
		return compressionThreshold > 0;
	}
	
	protected static int readSInt32(InputStream in) throws IOException {
		byte[] buf = new byte[4];
		int len = in.read(buf, 0, buf.length);
		if (len != buf.length) {
			throw new EOFException("expected " + buf.length + " bytes, got " + len);
		}
		return ((int) (buf[0] & 0xff) << 24) | 
				((int) (buf[1] & 0xff) << 16) | 
				((int) (buf[2] & 0xff) << 8) | 
				((int) (buf[3] & 0xff));
	}

	protected static void writeSInt32(OutputStream out, int val) throws IOException {
		byte[] buf = {
				(byte) ((val >> 24) & 0xff), 
				(byte) ((val >> 16) & 0xff),
				(byte) ((val >> 8) & 0xff), 
				(byte) (val & 0xff)};		
		out.write(buf);
	}

	protected final void assertBeganRead() throws IOException
	{
		if (!rlock.isHeldByCurrentThread()) {
			throw new IOException("thread must first call beginRead");
		}
	}

	@Override
	public int beginRead() throws IOException {
		if (rlock.isHeldByCurrentThread()) {
			throw new IOException("beginRead is not reentrant");
		}
		
		logger.info("beginRead: acq lock...");
		rlock.lock();
		logger.info("beginRead: got lock");
		try {
			assert readStream == null;
			
			int seq = readSInt32(inStream);
			logger.info("beginRead: seq = " + seq);
			
			int packetLength = readSInt32(inStream);
			logger.info("beginRead: packetLength = " + packetLength);
			
			int uncompressedLength = readSInt32(inStream);
			logger.info("beginRead: uncompressedLength = " + uncompressedLength);
			
			readStream = new BoundedInputStream(inStream, packetLength, true, false);
			if (uncompressedLength > 0) {
				readStream = new BoundedInputStream(new InflaterInputStream(readStream),
						uncompressedLength, false, true);
			}
			
			return seq;
		}
		catch (IOException ex) {
			logger.info("XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX" + ex);
			logger.log(Level.WARNING, "beginRead", ex);
			readStream = null;
			rlock.unlock();
			close();
			throw ex;
		}
	}
	
	@Override
	public int read(byte[] buf, int off, int len) throws IOException {
		assertBeganRead();
		return readStream.read(buf, off, len);
	}

	@Override
	public void endRead() throws IOException {
		assertBeganRead();
		readStream.close();
		readStream = null;
		logger.info("endRead: releasing lock");
		rlock.unlock();
	}
	
	protected final void assertBeganWrite() throws IOException
	{
		if (!wlock.isHeldByCurrentThread()) {
			throw new IOException("thread must first call beginWrite");
		}
	}

	@Override
	public void beginWrite(int seq) throws IOException {
		if (wlock.isHeldByCurrentThread()) {
			throw new IOException("beginWrite is not reentrant");
		}
		
		logger.info("beginWrite: seq = " + seq + ", acq lock...");
		wlock.lock();
		logger.info("beginWrite: got lock");
		wbuffer.reset();
		wseq = seq;
	}
	
	@Override
	public void write(byte[] buf, int off, int len) throws IOException {
		assertBeganWrite();
		wbuffer.write(buf, off, len);
	}

	@Override
	public void restartWrite() throws IOException {
		assertBeganWrite();
		wbuffer.reset();
	}
	
	@Override
	public void endWrite() throws IOException {
		assertBeganWrite();
		int len = wbuffer.size();
		logger.info("endWrite: len = " + len);
		if (len > 0) {
			writeSInt32(outStream, wseq);
			
			if (compressionThreshold > 0 && len > compressionThreshold) {
				// compress
				compressionBuffer.reset();
				DeflaterOutputStream defl = new DeflaterOutputStream(compressionBuffer);
				wbuffer.writeTo(defl);
				defl.close(); // compressionBuffer is unharmed by close()
				
				writeSInt32(outStream, compressionBuffer.size()); // packetLength
				writeSInt32(outStream, len); // uncompressedLength
				compressionBuffer.writeTo(outStream);
			}
			else {
				// no compression
				writeSInt32(outStream, len); // packetLength
				writeSInt32(outStream, 0); // uncompressedLength <= 0 means no compression
				wbuffer.writeTo(outStream);
			}
			outStream.flush();
		}
		logger.info("endWrite: releasing lock");
		wlock.unlock();
	}
	
	/**
	 * cancels the currently active write transaction (nothing will be written 
	 * to the stream). you can issue a new beginWrite afterwards.
	 */
	@Override
	public void cancelWrite() throws IOException {
		assertBeganWrite();
		wbuffer.reset();
		logger.info("cancelWrite: releasing lock");
		wlock.unlock();
	}
}
