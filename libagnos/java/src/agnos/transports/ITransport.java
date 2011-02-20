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

import java.io.*;

/**
 * A transport is an object that provides transactional IO capabilities
 * 
 * @author Tomer Filiba
 * 
 */
public interface ITransport extends Closeable {
	/**
	 * closes the transport (including all the underlying operating-system
	 * resources)
	 */
	void close() throws IOException;

	/**
	 * returns a view of this Transport as an InputStream. note that you can use
	 * this InputStream only after beginRead() has been issued.
	 * issuing close() on the returned stream has the effect of endRead()
	 */
	InputStream getInputStream();

	/**
	 * returns a view of this Transport as an OutputStream. note that you can
	 * use this OutputStream only after beginWrite() has been issued.
	 * issuing close() on the returned stream has the effect of endWrite()
	 */
	OutputStream getOutputStream();

	/**
	 * returns a boolean indicating whether the stream is compressed or not.
	 * initially, compression is disabled.
	 */
	boolean isCompressionEnabled();

	/**
	 * enables compression of the stream; all packets longer than some threshold
	 * will be compressed (using the Deflate algorithm as defined by ZLIB) 
	 * before being sent to the other side.
	 * 
	 * note: initially, compression is disabled. you may enable it explicitly,
	 * after verifying that the other side supports compression.
	 * 
	 * returns true if compression has been enabled, false otherwise (i.e., 
	 * compression is not supported by underlying transport)
	 */
	boolean enableCompression();

	/**
	 * disables compression of the stream
	 */
	void disableCompression(); 
	
	//
	// read interface
	//

	/**
	 * begins a new read-transaction; this method would block until a
	 * transaction is received on the transport. Only a single thread can start
	 * a read transaction at any point of time; other threads calling
	 * beginRead() will block until the owning thread calls endRead().
	 * 
	 * Note: only a single read-transaction can be created at any point of time;
	 * it is not possible to call read() or endRead() before beginRead() returns
	 * 
	 * @return the sequence number of the incoming transaction
	 */
	int beginRead() throws IOException;

	/**
	 * reads up to `len` bytes of data from the underlying input stream, into
	 * `data` starting from `offset`.
	 * 
	 * Note: may only be called after beginRead() has been called.
	 * 
	 * @param data
	 *            the array that will hold the read data
	 * @param offset
	 *            the offset into the `data` array (normally 0), from which read
	 *            data will be stored
	 * @param len
	 *            the number of bytes to read (the number of actual bytes read
	 *            may be lower)
	 * 
	 * @return the actual number of bytes read
	 */
	int read(byte[] data, int offset, int len) throws IOException;

	/**
	 * ends the current read transaction. May be called only after beginRead()
	 * has been issued. another call to beginRead() will not be possible until
	 * endRead() has been called.
	 * 
	 * Note: may only be called after beginRead() has been called.
	 */
	void endRead() throws IOException;

	//
	// write interface
	//

	/**
	 * begins a write transaction with the given sequence number. only a single
	 * thread can issue a write-transaction at any given time; other threads
	 * calling beginWrite() will block until the owning thread calls endWrite().
	 * 
	 * Note: only a single write-transaction can be created at any point of
	 * time; it is not possible to call write(), reset(), endWrite() or
	 * cancelWrite() before issuing a beginWrite()
	 * 
	 * @param seq
	 *            The sequence number of this tranaction
	 */
	void beginWrite(int seq) throws IOException;

	/**
	 * writes `len` bytes from the `data` array, starting at `offset`. The
	 * method does not directly send data -- it only stores it in an internal
	 * buffer, until endWrite() is called.
	 * 
	 * Note: may be called only after beginWrite()
	 * 
	 * @param data
	 *            the array from which data will be written
	 * @param offset
	 *            the offset into the array, from which to start
	 * @param len
	 *            the number of bytes to be written
	 */
	void write(byte[] data, int offset, int len) throws IOException;

	/**
	 * discards all the data written so far to the current transaction (the
	 * transaction itself is not cancelled, only it's data is discarded)
	 * 
	 * Note: may be called only after beginWrite()
	 */
	void restartWrite() throws IOException;

	/**
	 * sends the data written so far and ends the current transaction.
	 * 
	 * Note: may be called only after beginWrite()
	 */
	void endWrite() throws IOException;

	/**
	 * cancels the current transaction (like a combination of reset() followed
	 * by endWrite())
	 * 
	 * Note: may be called only after beginWrite()
	 */
	void cancelWrite() throws IOException;
}
