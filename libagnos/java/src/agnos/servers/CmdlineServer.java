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

import agnos.protocol.IProcessorFactory;
import agnos.transportFactories.SocketTransportFactory;


public class CmdlineServer
{
	protected IProcessorFactory processorFactory;

	public static class SwitchException extends Exception
	{
		private static final long serialVersionUID = 6612636232151491349L;

		public SwitchException(String message)
		{
			super(message);
		}
	}
	
	protected static enum ServingMode
	{
		SIMPLE, THREADED, LIB
	}

	public CmdlineServer(IProcessorFactory processorFactory)
	{
		this.processorFactory = processorFactory;
	}

	public void main(String[] args) throws Exception
	{
		ServingMode mode = ServingMode.SIMPLE;
		String host = "127.0.0.1";
		int port = 0;

		for (int i = 0; i < args.length; i += 1) {
			String arg = args[i];
			if (arg.equals("-m")) {
				i += 1;
				if (i >= args.length) {
					throw new SwitchException("-m requires an argument");
				}
				arg = args[i].toLowerCase();
				if (arg.equals("lib") || arg.equals("library")) {
					mode = ServingMode.LIB;
				}
				else if (arg.equals("simple")) {
					mode = ServingMode.SIMPLE;
				}
				else if (arg.equals("threaded")) {
					mode = ServingMode.THREADED;
				}
				else {
					throw new SwitchException("invalid mode: " + arg);
				}
			}
			else if (arg.equals("-h")) {
				i += 1;
				if (i >= args.length) {
					throw new SwitchException("-h requires an argument");
				}
				host = args[i];
			}
			else if (arg.equals("-p")) {
				i += 1;
				if (i >= args.length) {
					throw new SwitchException("-p requires an argument");
				}
				port = Integer.parseInt(args[i]);
			}
			else {
				throw new SwitchException("invalid switch: " + arg);
			}
		}

		BaseServer server = null;

		switch (mode) {
		case SIMPLE:
			if (port == 0) {
				throw new SwitchException(
						"simple server requires specifying a port");
			}
			server = new SimpleServer(processorFactory, 
					new SocketTransportFactory(host, port));
			break;
		case THREADED:
			if (port == 0) {
				throw new SwitchException(
						"threaded server requires specifying a port");
			}
			server = new ThreadedServer(processorFactory,
					new SocketTransportFactory(host, port));
			break;
		case LIB:
			server = new LibraryModeServer(processorFactory,
					new SocketTransportFactory(host, port));
			break;
		default:
			throw new SwitchException("invalid mode: " + mode);
		}

		server.serve();
	}
}
