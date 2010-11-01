// ////////////////////////////////////////////////////////////////////////////
// Part of the Agnos RPC Framework
// http://agnos.sourceforge.net
//
// Copyright 2010, Tomer Filiba (tomerf@il.ibm.com; tomerfiliba@gmail.com)
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

package agnos;

import java.io.*;
import java.util.*;
import java.net.*;
import javax.net.ssl.*;


public class TransportFactories
{
	public interface ITransportFactory
	{
		void close() throws IOException;

		Transports.ITransport accept() throws IOException;
	}

	public static class SocketTransportFactory implements ITransportFactory
	{
		protected final static int DEFAULT_BACKLOG = 10;
		
		protected ServerSocket serverSocket;

		public SocketTransportFactory(int port) throws IOException
		{
			this(port, DEFAULT_BACKLOG);
		}

		public SocketTransportFactory(int port, int backlog) throws IOException
		{
			this(InetAddress.getLocalHost(), port, backlog);
		}

		public SocketTransportFactory(String host, int port) throws IOException
		{
			this(host, port, DEFAULT_BACKLOG);
		}

		public SocketTransportFactory(String host, int port, int backlog)
				throws IOException
		{
			this(InetAddress.getByName(host), port, backlog);
		}

		public SocketTransportFactory(InetAddress addr, int port, int backlog)
				throws IOException
		{
			this(new ServerSocket(port, backlog, addr));
		}

		public SocketTransportFactory(ServerSocket serverSocket)
		{
			this.serverSocket = serverSocket;
		}
		
		public void close() throws IOException
		{
			serverSocket.close();
		}

		public Transports.ITransport accept() throws IOException
		{
			return new Transports.SocketTransport(serverSocket.accept());
		}
	}

	public static class SSLSocketTransportFactory extends SocketTransportFactory
	{
		public SSLSocketTransportFactory(int port) throws IOException
		{
			this(port, DEFAULT_BACKLOG);
		}

		public SSLSocketTransportFactory(int port, int backlog) throws IOException
		{
			this(InetAddress.getLocalHost(), port, backlog);
		}

		public SSLSocketTransportFactory(String host, int port) throws IOException
		{
			this(host, port, DEFAULT_BACKLOG);
		}
		
		public SSLSocketTransportFactory(String host, int port, int backlog) throws IOException
		{
			this((SSLServerSocketFactory)SSLServerSocketFactory.getDefault(), 
					InetAddress.getByName(host), port, backlog);
		}
		
		public SSLSocketTransportFactory(InetAddress addr, int port, int backlog) throws IOException
		{
			this((SSLServerSocketFactory)SSLServerSocketFactory.getDefault(), 
					addr, port, backlog);
		}

		public SSLSocketTransportFactory(SSLServerSocketFactory factory, 
				InetAddress addr, int port, int backlog) throws IOException
		{
			this((SSLServerSocket)factory.createServerSocket(port, backlog, addr));
		}
		
		public SSLSocketTransportFactory(SSLServerSocket serverSocket)
		{
			super(serverSocket);
		}
	}

}







































