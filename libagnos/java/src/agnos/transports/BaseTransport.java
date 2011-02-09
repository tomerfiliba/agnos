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
import agnos.util.ClosedOutputStream;
import agnos.util.ClosedInputStream;
import agnos.packers.Builtin;


/**
 * The base transport class -- implements the common logic used by most (if 
 * not all) derived transports.
 * 
 * @author Tomer Filiba
 *
 */
public abstract class BaseTransport implements ITransport
	protected final static int INITIAL_BUFFER_CAPACITY = 128 * 1024; 
		
	protected InputStream inStream;
	protected OutputStream outStream;
	protected final ReentrantLock rlock = new ReentrantLock();
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
			byte[] buffer = { (byte) b };
			write(buffer);
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
	
	public BaseTransport(InputStream inStream, OutputStream outStream) {
		this.inStream = inStream;
		this.outStream = outStream;
	}
	
	@Override
	public void close() throws IOException {
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
	public int isCompressionEnabled() {
		return compressionThreshold > 0;
	}
	
	protected static int readSInt32(InputStream in) throws IOException {
		byte[] buf = new byte[4];
		int len = in.read(buf, 0, buf.length);
		if (len != buf.length) {
			throw new EOFException("expected " + buf.length + " bytes, got " + len);
		}
		return ((int) (buf[0] & 0xff) << 24) | ((int) (buf[1] & 0xff) << 16) | 
			((int) (buf[2] & 0xff) << 8) | ((int) (buf[3] & 0xff));
	}

	protected static void writeSInt32(OutputStream out, int val) throws IOException {
		byte[] buf = {(byte) ((val >> 24) & 0xff), (byte) ((val >> 16) & 0xff),
				(byte) ((val >> 8) & 0xff), (byte) (val & 0xff)};		
		out.write(buf, 0, buf.length);
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

		rlock.lock();
		assert readStream == null;
		
		int seq = readSInt32(inStream);
		int packetLength = readSInt32(inStream);
		int uncompressedLength = readSInt32(inStream);
		if (uncompressedLength <= 0) {
			// no compression
			readStream = new BoundedInputStream(inStream, packetLength, false);
		}
		else {
			// compressed stream
			InputStream inf = new InflaterInputStream(
					new BoundedInputStream(inStream, packetLength, false));
			readStream = new BoundedInputStream(inf, uncompressedLength, true);
		}
		
		return seq;
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
		
		wlock.lock();
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
		wlock.unlock();
	}
}
