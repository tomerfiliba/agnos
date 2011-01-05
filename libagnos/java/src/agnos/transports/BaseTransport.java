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
import java.io.EOFException;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.util.concurrent.locks.ReentrantLock;
import java.util.zip.DeflaterOutputStream;

import agnos.packers.Builtin;


/**
 * The base transport class -- implements the common logic used by most (if 
 * not all) derived transports.
 * 
 * @author Tomer Filiba
 *
 */
public abstract class BaseTransport implements ITransport
{
	// write buffer
	protected ByteArrayOutputStream buffer;
	// compression buffer
	protected ByteArrayOutputStream buffer2;
	// the input stream
	protected InputStream input;
	// decompressed input-stream
	protected InputStream input2;
	// the output stream
	protected OutputStream output;
	// locks that are used to sync reading and writing
	protected ReentrantLock rlock;
	protected ReentrantLock wlock;
	// cached InputStream and OutputStream adapters
	protected InputStream asInputStream;
	protected OutputStream asOutputStream;

	// write sequence number
	protected int wseq; 
	// read sequence number
	protected int rseq;
	// read position (within the current packet)
	protected int rpos;
	// read length (size of physical packet)
	protected int rlength;
	// decompressed length (size of packet after decompression)
	protected int rcomplength;
	// compression threshold. if negative, compression is disabled
	protected int compressionThreshold;

	// initial size of write buffers
	protected static final int DEFAULT_BUFFER_SIZE = 128 * 1024;

	/**
	 * An adapter class for getInputStream() that makes the transport object
	 * look like an InputStream.
	 */
	protected static final class TransportInputStream extends InputStream
	{
		ITransport transport;

		public TransportInputStream(ITransport transport)
		{
			this.transport = transport;
		}

		@Override
		public int read() throws IOException
		{
			byte[] buffer = { 0 };
			read(buffer);
			return buffer[0];
		}

		@Override
		public int read(byte[] data, int off, int len) throws IOException
		{
			return transport.read(data, off, len);
		}
	}

	/**
	 * An adapter class for getOutStream() that makes the transport object
	 * look like an OutputStream.
	 */
	protected static final class TransportOutputStream extends OutputStream
	{
		ITransport transport;

		public TransportOutputStream(ITransport transport)
		{
			this.transport = transport;
		}

		@Override
		public void write(int b) throws IOException
		{
			byte[] buffer = { (byte) b };
			write(buffer);
		}

		@Override
		public void write(byte[] data, int off, int len) throws IOException
		{
			transport.write(data, off, len);
		}
	}
	
	/*protected static String repr(byte[] arr, int off, int len)
	{
		StringBuffer sb = new StringBuffer(len*2);
		int end = Math.min(arr.length, off+len);
		for (int i = off; i < end; i++) {
			if (arr[i] < 32 || arr[i] > 126) {
				sb.append(String.format("\\x%02x", arr[i])); 
			}
			else {
				sb.append((char)(arr[i]));
			}
		}
		return sb.toString();
	}

	protected static String repr(byte[] arr)
	{
		return repr(arr, 0, arr.length);
	}*/
	

	/**
	 * Constructs a Transport object from an input stream and an output stream.
	 * 
	 * @param input		an input stream (to be used for read operations)
	 * 
	 * @param output		an output stream (to be used for write operations)
	 * 
	 * @param compressionThreshold	an integer specifying the minimal packet
	 * 		length that should be compressed. You can set it to a negative 
	 * 		number (-1) to disable compression. The value of this parameter
	 * 		is usually determined by the actual transport: for instance, for 
	 * 		sockets, it would normally make sense to compress packets that are
	 * 		longer than the ethernet MTU.
	 */
	public BaseTransport(InputStream input, OutputStream output,
			int compressionThreshold)
	{
		this.input = input;
		this.output = output;
		this.compressionThreshold = -1; // compressionThreshold;
		input2 = null;
		buffer = new ByteArrayOutputStream(DEFAULT_BUFFER_SIZE);
		buffer2 = new ByteArrayOutputStream(DEFAULT_BUFFER_SIZE);
		wlock = new ReentrantLock();
		rlock = new ReentrantLock();
		asInputStream = new TransportInputStream(this);
		asOutputStream = new TransportOutputStream(this);
	}

	@Override
	public void close() throws IOException
	{
		// System.out.printf("[%s.close]\n", this);
		if (input != null) {
			input.close();
			input = null;
		}
		if (output != null) {
			output.close();
			output = null;
		}
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

	//
	// read interface
	//
	@Override
	public synchronized int beginRead() throws IOException
	{
		return beginRead(-1);
	}

	@Override
	public synchronized int beginRead(int msecs) throws IOException
	{
		// System.out.printf("[%s.beginRead] ", this);
		if (rlock.isHeldByCurrentThread()) {
			throw new IOException("beginRead is not reentrant");
		}

		rlock.lock();
		rseq = (Integer) Builtin.Int32.unpack(input);
		rlength = (Integer) Builtin.Int32.unpack(input);
		rcomplength = (Integer) Builtin.Int32.unpack(input);
		rpos = 0;
		// System.out.printf("length = %d, seq = %d, compressed = %s\n",
		// rlength, rseq, (rcomplength > 0) ? "T" : "F");

		// if (rcomplength > 0) {
		// input2 = new InflaterInputStream(input);
		// int tmp = rlength;
		// rlength = rcomplength;
		// rcomplength = tmp;
		// }
		// else {
		input2 = input;
		// }

		return rseq;
	}

	protected void assertBeganRead() throws IOException
	{
		if (!rlock.isHeldByCurrentThread()) {
			throw new IOException("thread must first call beginRead");
		}
	}

	@Override
	public int read(byte[] data, int offset, int len) throws IOException
	{
		// System.out.printf("[%s.read(%d)] ", this, len);
		assertBeganRead();
		if (rpos + len > rlength) {
			throw new EOFException("request to read more than available");
		}
		int actually_read = input2.read(data, offset, len);
		// System.out.printf("%s\n", repr(data, offset, len));
		rpos += actually_read;
		return actually_read;
	}

	@Override
	public synchronized void endRead() throws IOException
	{
		// System.out.printf("[%s.endRead()]\n", this);
		assertBeganRead();
		input2.skip(rlength - rpos);
		rlock.unlock();
		input2 = null;
	}

	//
	// write interface
	//
	@Override
	public synchronized void beginWrite(int seq) throws IOException
	{
		// System.out.printf("[%s.beginWrite(%d)]\n", this, seq);
		if (wlock.isHeldByCurrentThread()) {
			throw new IOException("beginWrite is not reentrant");
		}
		wlock.lock();
		wseq = seq;
		buffer.reset();
	}

	protected void assertBeganWrite() throws IOException
	{
		if (!wlock.isHeldByCurrentThread()) {
			throw new IOException("thread must first call beginWrite");
		}
	}

	@Override
	public void write(byte[] data, int offset, int len) throws IOException
	{
		// System.out.printf("[%s.write(%d)] %s\n", this, len,
		// repr(data, offset, len));
		assertBeganWrite();
		buffer.write(data, offset, len);
	}

	@Override
	public void reset() throws IOException
	{
		// System.out.printf("[%s.reset()]\n", this);
		assertBeganWrite();
		buffer.reset();
	}

	@Override
	public synchronized void endWrite() throws IOException
	{
		int len = buffer.size();
		// System.out.printf("[%s.endWrite(%d)] ", this, len);
		assertBeganWrite();

		if (len > 0) {
			Builtin.Int32.pack(wseq, output);

			if (compressionThreshold >= 0 && len > compressionThreshold) {
				buffer2.reset();
				DeflaterOutputStream comp = new DeflaterOutputStream(buffer2);
				buffer.writeTo(comp);
				comp.finish();

				// System.out.printf("compressed to %d\n", buffer2.size());
				Builtin.Int32.pack(buffer2.size(), output); // actual size
				Builtin.Int32.pack(len, output); // uncompressed size
				buffer2.writeTo(output);
			}
			else {
				// System.out.printf("uncompressed\n");

				Builtin.Int32.pack(len, output); // actual size
				Builtin.Int32.pack(0, output); // 0 means no compression
				buffer.writeTo(output);
			}

			output.flush();
			buffer.reset();
		}
		wlock.unlock();
	}

	@Override
	public synchronized void cancelWrite() throws IOException
	{
		// System.out.printf("[%s.cancelWrite()]\n", this);
		assertBeganWrite();
		buffer.reset();
		wlock.unlock();
	}
}
