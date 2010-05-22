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
				ITransport transport = transportFactory.accept();
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
                while (true)
                {
                    processor.process(inStream, outStream);
                }
            }
            catch (EndOfStreamException)
            {
                // finish on EOF
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

    public class LibraryModeServer
    {
        internal TcpListener listener;
        protected Protocol.BaseProcessor processor;

        public LibraryModeServer(Protocol.BaseProcessor processor) :
            this(processor, IPAddress.Loopback)
        {
        }

        public LibraryModeServer(Protocol.BaseProcessor processor, IPAddress addr)
        {
            this.processor = processor;
            listener = new TcpListener(addr, 0);
        }

        public void serve()
        {
            listener.Start(1);
            IPEndPoint ep = (IPEndPoint)listener.LocalEndpoint;
            System.Console.Out.Write("{0}\n{1}\n", ep.Address, ep.Port);
            System.Console.Out.Flush();
            System.Console.Out.Close();
            listener.Stop();

            ITransport transport = new SocketTransport(listener.AcceptSocket());
            BaseServer.serveClient(processor, transport);
        }
    }
}
