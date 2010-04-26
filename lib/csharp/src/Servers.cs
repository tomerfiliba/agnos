using System;
using System.IO;
using System.Net;
using System.Net.Sockets;
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
		
		public void serve()
		{
			while (true)
			{
				ITransport transport = transportFactory.accept();
				System.Console.WriteLine("accepted: " + transport);
				_handleClient(transport);
				System.Console.WriteLine("goodbye");
			}
		}

		protected abstract void _handleClient(ITransport transport);
	}

	public class SimpleServer : BaseServer
	{
		public SimpleServer(Protocol.BaseProcessor processor, ITransportFactory transportFactory) :
			base(processor, transportFactory)
		{
		}

		protected override void _handleClient(ITransport transport)
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
			catch (EndOfStreamException )
			{
				// finish on EOF
			}
		}
	}

	/*public class ThreadedServer : BaseServer
	{
		public ThreadedServer(Protocol.BaseProcessor processor, ITransportFactory transportFactory) :
			base(processor, transportFactory)
		{
		}

		protected override void _handleClient(ITransport transport)
		{
			Stream inStream = transport.getInputStream();
			Stream outStream = transport.getOutputStream();
		}
	}*/
}
