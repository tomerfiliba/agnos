// ////////////////////////////////////////////////////////////////////////////
// Part of the Agnos RPC Framework
// http://agnos.sourceforge.net
//
// Copyright 2011, International Business Machines Corp.
// Author: Tomer Filiba (tomerf@il.ibm.com)
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
// http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.
// ////////////////////////////////////////////////////////////////////////////

package agnos.transports;

import java.io.IOException;

import javax.net.ssl.SSLSocket;
import javax.net.ssl.SSLSocketFactory;



/**
 * A transport that operates over SSL-enabled sockets
 * 
 * @author Tomer Filiba
 * 
 * @see SocketTransport
 * 
 */
public class SSLSocketTransport extends SocketTransport
{
	/**
	 * Constructs an SSLSocketTransport from a host (given as string) and
	 * port number; uses default compression threshold and default
	 * SSLSocketFactory
	 * 
	 * @param host
	 *            The host to connect to
	 * @param port
	 *            The port number (TCP)
	 */
	public SSLSocketTransport(String host, int port) throws IOException
	{
		this(host, port, DEFAULT_BUFFER_SIZE);
	}

	/**
	 * Constructs an SSLSocketTransport from a host (given as string),
	 * port number, explicit internal buffering size
	 * 
	 * @param host
	 *            The host to connect to
	 * @param port
	 *            The port number (TCP)
	 * @param bufsize
	 *            Buffering size (for BufferedInputStream and
	 *            BufferedOutputStream)
	 * 
	 * @see SocketTransport
	 */
	public SSLSocketTransport(String host, int port, int bufsize) throws IOException
	{
		this((SSLSocket) (SSLSocketFactory.getDefault()
				.createSocket(host, port)), bufsize);
	}

	/**
	 * Constructs an SSLSocketTransport from an instance of SSLSocket.
	 * This allows you to use your own SSLSocketFactory.
	 * 
	 * @param sock
	 *            An pre-configured instance of SSLSocket
	 */
	public SSLSocketTransport(SSLSocket sock) throws IOException
	{
		this(sock, DEFAULT_BUFFER_SIZE);
	}

	/**
	 * Constructs an SSLSocketTransport from a host (given as string),
	 * port number, explicit internal buffering size, and compression
	 * threshold
	 * 
	 * @param sock
	 *            An pre-configured instance of SSLSocket
	 * @param bufsize
	 *            Buffering size (for BufferedInputStream and
	 *            BufferedOutputStream)
	 */
	public SSLSocketTransport(SSLSocket sock, int bufsize) throws IOException
	{
		super(sock, bufsize);
	}
}
