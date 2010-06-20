using System;
using System.IO;
using System.Net;
using System.Net.Sockets;
using System.Threading;
using System.Collections.Generic;
using Agnos.Transports;


namespace Agnos.Servers
{	
	public abstract class BaseServer
	{
		protected Protocol.BaseProcessor processor;
		protected ITransportFactory transportFactory;
		
		public BaseServer(Protocol.BaseProcessor processor, ITransportFactory transportFactory)
		{
			this.processor = processor;
			this.transportFactory = transportFactory;
		}
		
		virtual public void serve()
		{
			while (true)
			{
				ITransport transport = transportFactory.Accept();
				acceptClient(transport);
			}
		}

        protected abstract void acceptClient(ITransport transport);

        internal static void serveClient(Protocol.BaseProcessor processor, ITransport transport)
        {
            Stream inStream = transport.getInputStream();
            Stream outStream = transport.getOutputStream();

            try
            {
				processor.handshake(inStream, outStream);
                while (true)
                {
                    processor.process(inStream, outStream);
                }
            }
            catch (EndOfStreamException)
            {
                // finish on EOF
            }
			finally 
			{
				inStream.Close();
				outStream.Close();
			}
        }
    }

	public class SimpleServer : BaseServer
	{
		public SimpleServer(Protocol.BaseProcessor processor, ITransportFactory transportFactory) :
			base(processor, transportFactory)
		{
		}

        protected override void acceptClient(ITransport transport)
		{
            serveClient(processor, transport);
		}
	}

    public class ThreadedServer : BaseServer
    {
        //List<Thread> client_threads;

        public ThreadedServer(Protocol.BaseProcessor processor, ITransportFactory transportFactory) :
            base(processor, transportFactory)
        {
            //client_threads = new List<Thread>();
        }

        protected override void acceptClient(ITransport transport)
        {
            Thread t = new Thread(new ParameterizedThreadStart(threadproc));
            t.Start();
            //client_threads.Add(t);
            //t.IsAlive
        }

        protected void threadproc(object obj)
        {
            serveClient(processor, (ITransport)obj);
        }
    }

    public class LibraryModeServer : BaseServer
    {
        internal TcpListener listener;

		public LibraryModeServer(Protocol.BaseProcessor processor) : 
			this(processor, new Transports.SocketTransportFactory("127.0.0.1", 0))
        {
        }

		public LibraryModeServer(Protocol.BaseProcessor processor, SocketTransportFactory transportFactory) :
            base(processor, transportFactory)
        {
        }

        public override void serve()
        {
			TcpListener listener = ((SocketTransportFactory)transportFactory).listener;
            IPEndPoint ep = (IPEndPoint)listener.LocalEndpoint;
			
            System.Console.Out.Write("{0}\n{1}\n", ep.Address, ep.Port);
            System.Console.Out.Flush();
			// XXX: i can't seem to find a way to actually close the underlying
			// filedesc, so you have to use readline() instead of read()
			// because read() will block indefinitely
            System.Console.Out.Close();
            ITransport transport = transportFactory.Accept();
            transportFactory.Close();
			
            serveClient(processor, transport);
        }

		protected override void acceptClient(ITransport transport)
		{
		}
    }
	
	public class CmdlineServer
	{
		protected Protocol.BaseProcessor processor;
		
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
		
		public CmdlineServer(Protocol.BaseProcessor processor)
		{
			this.processor = processor;
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
					server = new SimpleServer(processor, 
					                          new Transports.SocketTransportFactory((string)options["host"], (int)options["port"]));
					break;
				case ServingMode.THREADED:
					if ((int)options["port"] == 0) {
						throw new ArgumentException("threaded mode requires specifying a port");
					}
					server = new ThreadedServer(processor, 
					                            new Transports.SocketTransportFactory((string)options["host"], (int)options["port"]));
					break;
				case ServingMode.LIB:
					server = new LibraryModeServer(processor, 
					                               new Transports.SocketTransportFactory((string)options["host"], (int)options["port"]));
					break;
				default:
					throw new ArgumentException("invalid mode: " + mode);
			}
			
			server.serve();
		}
	}
	
}
