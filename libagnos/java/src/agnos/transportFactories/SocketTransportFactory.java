// ////////////////////////////////////////////////////////////////////////////
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
// ////////////////////////////////////////////////////////////////////////////

package agnos.transportFactories;

import java.io.IOException;
import java.net.InetAddress;
import java.net.ServerSocket;

import agnos.transports.SocketTransport;
import agnos.transports.ITransport;



/**
 * A transport factory that uses good-old sockets 
 * 
 * @author Tomer Filiba
 */
public class SocketTransportFactory implements ITransportFactory
{
	protected final static int DEFAULT_BACKLOG = 10;
	
	protected ServerSocket serverSocket;

	/**
	 * Constructs a TCP SocketTransportFactory listening on the localhost at
	 * the given port with the default backlog
	 */
	public SocketTransportFactory(int port) throws IOException
	{
		this(port, DEFAULT_BACKLOG);
	}

	/**
	 * Constructs a TCP SocketTransportFactory listening on the localhost at
	 * the given port with the given backlog
	 */
	public SocketTransportFactory(int port, int backlog) throws IOException
	{
		this(InetAddress.getLocalHost(), port, backlog);
	}

	/**
	 * Constructs a TCP SocketTransportFactory listening on the given hostname 
	 * (interface) at the given port with the default backlog
	 */
	public SocketTransportFactory(String host, int port) throws IOException
	{
		this(host, port, DEFAULT_BACKLOG);
	}

	/**
	 * Constructs a TCP SocketTransportFactory listening on the given hostname 
	 * (interface) at the given port with the given backlog
	 */
	public SocketTransportFactory(String host, int port, int backlog)
			throws IOException
	{
		this(InetAddress.getByName(host), port, backlog);
	}

	/**
	 * Constructs a TCP SocketTransportFactory listening on the InetAddress
	 * at the given port with the given backlog
	 */
	public SocketTransportFactory(InetAddress addr, int port, int backlog)
			throws IOException
	{
		this(new ServerSocket(port, backlog, addr));
	}

	/**
	 * Constructs a SocketTransportFactory from an instance of a pre-configured
	 * ServerSocket
	 */
	public SocketTransportFactory(ServerSocket serverSocket)
	{
		this.serverSocket = serverSocket;
	}
	
	@Override
	public void close() throws IOException
	{
		serverSocket.close();
	}

	@Override
	public ITransport accept() throws IOException
	{
		return new SocketTransport(getServerSocket().accept());
	}

	public ServerSocket getServerSocket()
	{
		return serverSocket;
	}
}




