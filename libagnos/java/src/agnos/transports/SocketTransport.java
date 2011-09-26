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

import java.io.BufferedInputStream;
import java.io.BufferedOutputStream;
import java.io.IOException;
import java.net.Socket;


/**
 * A transport that operates over good-old sockets (normally TCP, but any
 * other stream protocol should work).
 * 
 * @author Tomer Filiba
 */
public class SocketTransport extends BaseTransport
{
	public static final int DEFAULT_BUFFER_SIZE = 32 * 1024;

	/**
	 * Constructs a TCP SocketTransport from a host (given as string) and
	 * port number
	 * 
	 * @param host
	 *            The host to connect to
	 * @param port
	 *            The port number (TCP)
	 */
	public SocketTransport(String host, int port) throws IOException
	{
		this(host, port, DEFAULT_BUFFER_SIZE);
	}

	/**
	 * Constructs a TCP SocketTransport from a host (given as string) and
	 * port number, explicit internal buffering size
	 * 
	 * @param host
	 *            The host to connect to
	 * @param port
	 *            The port number (TCP)
	 * @param bufsize
	 *            Buffering size (for BufferedInputStream and
	 *            BufferedOutputStream)
	 */
	public SocketTransport(String host, int port, int bufsize) throws IOException
	{
		this(new Socket(host, port), bufsize);
	}

	/**
	 * Constructs a SocketTransport from a given, pre-configured socket.
	 * Allows you to use any protocol you desire and customize various other
	 * parameters.
	 * 
	 * @param sock
	 *            The pre-configured socket instance
	 */
	public SocketTransport(Socket sock) throws IOException
	{
		this(sock, DEFAULT_BUFFER_SIZE);
	}

	/**
	 * Constructs a SocketTransport from a given, pre-configured socket,
	 * explicit internal buffering size, and compression threshold.
	 * Allows you to use any protocol you desire and customize various other
	 * parameters. 
	 * 
	 * @param sock
	 *            The pre-configured socket instance
	 * @param bufsize
	 *            Buffering size (for BufferedInputStream and
	 *            BufferedOutputStream)
	 */
	public SocketTransport(Socket sock, int bufsize)
			throws IOException
	{
		super(new BufferedInputStream(sock.getInputStream(), bufsize),
				new BufferedOutputStream(sock.getOutputStream(), bufsize));
	}
	
	@Override
	protected int getCompressionThreshold() {
		return -1; //4 * 1024;
	}
	
}
