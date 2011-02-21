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

using System;
using System.IO;
using System.Net;
using System.Net.Sockets;
using System.Threading;
using System.Collections.Generic;
using Agnos.Transports;
using Agnos.TransportFactories;


namespace Agnos.Servers
{	
	/// <summary>
	/// The base class of all Agnos servers. note that you're not required
	/// to extend this class in order to be implement a server -- it's just
	/// a place to store all of the common logic
	/// </summary>
	public abstract class BaseServer
	{
		protected Protocol.IProcessorFactory processorFactory;
		protected ITransportFactory transportFactory;
		
		public BaseServer(Protocol.IProcessorFactory processorFactory, ITransportFactory transportFactory)
		{
			this.processorFactory = processorFactory;
			this.transportFactory = transportFactory;
		}
		
		virtual public void Serve()
		{
			while (true)
			{
				ITransport transport = transportFactory.Accept();
				Protocol.BaseProcessor processor = processorFactory.Create(transport);
				serveClient(processor);
			}
		}

		/// <summary>
		/// implement this method to serve the client in whatever which way
		/// is appropriate (blocking, threaded, forking, threadpool, ...)
		/// </summary>
		/// <param name="processor">
		/// the processor instance that represents the client
		/// </param>
	    protected abstract void serveClient(Protocol.BaseProcessor processor);

		/// <summary>
		/// the basic client handler -- calls processor.process in a loop, 
		/// until the client disconnects
		/// </summary>
		/// <param name="processor">
		/// the processor instance that represents the client
		/// </param>
	    protected static void handleClient(Protocol.BaseProcessor processor)
        {
            try
            {
                while (true)
                {
                    processor.process();
                }
            }
            catch (EndOfStreamException)
            {
                // finish on EOF
            }
            catch (IOException)
            {
                // usually a "connection reset by peer" -- just clean up nicely,
                // the connection is dead anyway
            }
            finally 
			{
                processor.Close();
			}
        }
    }

	/// <summary>
	/// the SimpleServer can handle a single client at any point of time
	/// </summary>
	public class SimpleServer : BaseServer
	{
		public SimpleServer(Protocol.IProcessorFactory processorFactory, ITransportFactory transportFactory) :
			base(processorFactory, transportFactory)
		{
		}

        protected override void serveClient(Protocol.BaseProcessor processor)
		{
            handleClient(processor);
		}
	}

	/// <summary>
	/// creates a thread-per-client to handle each client in parallel
	/// </summary>
    public class ThreadedServer : BaseServer
    {
        //List<Thread> client_threads;

        public ThreadedServer(Protocol.IProcessorFactory processorFactory, ITransportFactory transportFactory) :
            base(processorFactory, transportFactory)
        {
            //client_threads = new List<Thread>();
        }

        protected override void serveClient(Protocol.BaseProcessor processor)
        {
            Thread t = new Thread(threadproc);
            t.Start(processor);
            //client_threads.Add(t);
        }

        protected void threadproc(object obj)
        {
            handleClient((Protocol.BaseProcessor)obj);
        }
    }

	/// <summary>
	/// the library-mode server -- opens an arbitrary socket, writes its 
	/// details (host and port number) to stdout, and serves for a single
	/// connection on that socket. when the connection is closed, the server
	/// quits and the application will usually terminate
	/// </summary>
    public class LibraryModeServer : BaseServer
    {
		public LibraryModeServer(Protocol.IProcessorFactory processorFactory) : 
			this(processorFactory, new SocketTransportFactory("127.0.0.1", 0))
        {
        }

		public LibraryModeServer(Protocol.IProcessorFactory processorFactory, SocketTransportFactory transportFactory) :
            base(processorFactory, transportFactory)
        {
        }

        public override void Serve()
        {
			TcpListener listener = ((SocketTransportFactory)transportFactory).listener;
            IPEndPoint ep = (IPEndPoint)listener.LocalEndpoint;
			
            System.Console.Out.Write("AGNOS\n{0}\n{1}\n", ep.Address, ep.Port);
            System.Console.Out.Flush();
			// XXX: i can't seem to find a way to actually close the underlying
			// filedesc, so we have to use readline() instead of read()
			// because read() will block indefinitely
            System.Console.Out.Close();
            ITransport transport = transportFactory.Accept();
            transportFactory.Close();
			
            Protocol.BaseProcessor processor = processorFactory.Create(transport);
            handleClient(processor);
        }

		protected override void serveClient(Protocol.BaseProcessor processor)
		{
			throw new InvalidOperationException("should never be called");
		}
    }
	
	/// <summary>
	/// command-line server. provides a common Main() function for the application
	/// that parses command-line options and invokes the appropriate server, until
	/// it quits
	/// </summary>
	public class CmdlineServer
	{
		protected Protocol.IProcessorFactory processorFactory;
		
		protected delegate object ArgType(String value);
		
		protected class ArgSpec
		{
			public string name;
			public ArgType type;
			public object defaultvalue = null;
			public bool optional = true;
			public string help = null;
		}
		
		protected static Dictionary<string, object> parse_args(Dictionary<string, ArgSpec> argspecs, string[] args)
		{
			Dictionary<string, object> output = new Dictionary<string, object>();
			ArgSpec spec;
			
			for(int i = 0; i < args.Length; i++)
			{
				string swch = args[i];
				if (argspecs.TryGetValue(swch, out spec)) {
					if (spec.type == null) {
						output.Add(spec.name, true);
					}
					else {
						i++;
						if (i >= args.Length) {
							throw new ArgumentException("switch " + swch + " requires an argument");
						}
						object val = spec.type(args[i]);
						output.Add(spec.name, val);
					}
				}
				else {
					throw new ArgumentException("invalid switch " + swch);
				}
			}
			
			foreach (KeyValuePair<string, ArgSpec> kvp in argspecs)
			{
				spec = kvp.Value;
				if (!output.ContainsKey(spec.name)) {
					if (spec.optional && spec.defaultvalue != null) {
						output.Add(spec.name, spec.defaultvalue);
					}
					else {
						throw new ArgumentException("required switch " + kvp.Key + " is missing");
					}
				}
			}
			
			return output;
		}
		
		protected enum ServingMode
		{
			SIMPLE,
			THREADED,
			LIB
		}
		
		public CmdlineServer(Protocol.IProcessorFactory processorFactory)
		{
			this.processorFactory = processorFactory;
		}
		
		public void Main(string[] args)
		{
			Dictionary<string, object> options = parse_args(new Dictionary<string, ArgSpec> {
				{"-m", new ArgSpec {
						name = "mode", 
						type = delegate(string val) {
							val = val.ToLower();
							if (val == "lib" || val == "library") {
								return ServingMode.LIB;
							}
							else if (val == "simple") {
								return ServingMode.SIMPLE;
							}
							else if (val == "threaded") {
								return ServingMode.THREADED;
							}
							else {
								throw new ArgumentException("invalid mode: " + val);
							}
						},
						defaultvalue = ServingMode.SIMPLE,
					}},
					{"-h", new ArgSpec {
						name = "host", 
						type = delegate(string val) {return val;},
						defaultvalue = "127.0.0.1",
					}},
					{"-p", new ArgSpec {
						name = "port", 
						type = delegate(string val) {return Int32.Parse(val);},
						defaultvalue = 0,
					}},
				},
				args);
			
			ServingMode mode = (ServingMode)options["mode"];
			BaseServer server = null;
			
			switch (mode)
			{
				case ServingMode.SIMPLE:
					if ((int)options["port"] == 0) {
						throw new ArgumentException("simple mode requires specifying a port");
					}
					server = new SimpleServer(processorFactory, 
					                          new SocketTransportFactory((string)options["host"], (int)options["port"]));
					break;
				case ServingMode.THREADED:
					if ((int)options["port"] == 0) {
						throw new ArgumentException("threaded mode requires specifying a port");
					}
					server = new ThreadedServer(processorFactory, 
					                            new SocketTransportFactory((string)options["host"], (int)options["port"]));
					break;
				case ServingMode.LIB:
					server = new LibraryModeServer(processorFactory, 
					                               new SocketTransportFactory((string)options["host"], (int)options["port"]));
					break;
				default:
					throw new ArgumentException("invalid mode: " + mode);
			}
			
			server.Serve();
		}
	}
	
}
