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

import java.io.EOFException;
import java.net.SocketException;

import agnos.protocol.BaseProcessor;
import agnos.protocol.IProcessorFactory;
import agnos.transportFactories.ITransportFactory;
import agnos.transports.ITransport;


public abstract class BaseServer
{
	protected IProcessorFactory processorFactory;
	protected ITransportFactory transportFactory;

	public BaseServer(IProcessorFactory processorFactory,
			ITransportFactory transportFactory)
	{
		this.processorFactory = processorFactory;
		this.transportFactory = transportFactory;
	}

	public void serve() throws Exception
	{
		while (true) {
			// System.err.println("accepting...");
			ITransport transport = transportFactory.accept();
			BaseProcessor processor = processorFactory.create(transport);
			serveClient(processor);
		}
	}

	protected abstract void serveClient(BaseProcessor processor) throws Exception;

	protected static void _serveClient(BaseProcessor processor) throws Exception
	{
		try {
			while (true) {
				processor.process();
			}
		} catch (EOFException exc) {
			// finish on EOF
		} catch (SocketException exc) {
			// System.out.println("!! SocketException: " + exc);
		} finally {
			processor.close();
		}
	}
}

