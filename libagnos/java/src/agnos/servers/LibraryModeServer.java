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

package agnos.servers;

import java.io.IOException;
import java.net.ServerSocket;
import java.net.UnknownHostException;

import agnos.protocol.BaseProcessor;
import agnos.protocol.IProcessorFactory;
import agnos.transportFactories.SocketTransportFactory;
import agnos.transports.ITransport;


public class LibraryModeServer extends BaseServer
{
	public LibraryModeServer(IProcessorFactory processorFactory)
			throws IOException, UnknownHostException
	{
		this(processorFactory, new SocketTransportFactory("127.0.0.1", 0));
	}

	public LibraryModeServer(IProcessorFactory processorFactory,
			SocketTransportFactory transportFactory)
			throws IOException
	{
		super(processorFactory, transportFactory);
	}

	@Override
	public void serve() throws Exception
	{
		ServerSocket serverSocket = ((SocketTransportFactory) transportFactory).getServerSocket();
		System.out.println("AGNOS");
		System.out.println(serverSocket.getInetAddress().getHostAddress());
		System.out.println(serverSocket.getLocalPort());
		System.out.flush();
		System.out.close();

		ITransport transport = transportFactory.accept();
		transportFactory.close();
		BaseProcessor processor = processorFactory.create(transport);
		_serveClient(processor);
	}

	@Override
	protected void serveClient(BaseProcessor processor) throws Exception
	{
		throw new AssertionError("should never be called");
	}
}

