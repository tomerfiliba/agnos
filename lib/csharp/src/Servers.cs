using System;
using System.IO;
using System.Net;
using System.Net.Sockets;


namespace Agnos.Servers
{
	public interface ITransport
	{
		Stream getInputStream();
		Stream getOutputStream();
	}

	public interface ITransportFactory
	{
		ITransport accept();
	}

	public class SocketTransportFactory : ITransportFactory
	{
		public const int backlog = 10;
		protected TcpListener listener;

		public SocketTransportFactory(int port) :
			this(IPAddress.Any, port)
		{
		}

		public SocketTransportFactory(String host, int port) :
			this(Dns.GetHostEntry(Dns.GetHostName()).AddressList[0], port)
		{
		}

		public SocketTransportFactory(IPAddress addr, int port)
		{
			listener = new TcpListener(addr, port);
			System.Console.WriteLine("listening on {0}:{1}", addr, port);
		}
		
		public ITransport accept()
		{
			System.Console.WriteLine("accepting...");
			return new SocketTransport(listener.AcceptSocket());
		}
	}
	
	public class SocketTransport : ITransport
	{
		protected Socket sock;
		public const int bufsize = 8000;
		
		public SocketTransport(Socket sock)
		{
			this.sock = sock;
		}
		
		private static Socket _ConnectSocket(string host, int port)
		{
			Socket sock = new Socket(AddressFamily.InterNetwork, SocketType.Stream, ProtocolType.Tcp);
			sock.Connect(host, port);
			return sock;
		}
		
		public SocketTransport(String host, int port) : 
			this(_ConnectSocket(host, port))
		{
		}
		
		public Stream getInputStream()
		{
			return new BufferedStream(new NetworkStream(sock), bufsize);
		}

		public Stream getOutputStream()
		{
			return new BufferedStream(new NetworkStream(sock), bufsize);
		}
	}
	
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
			catch (EndOfStreamException exc)
			{
				// finish on EOF
			}
			catch (SocketException exc)
			{
				System.Console.WriteLine("!! SocketException: " + exc);
			}
		}
	}

	public class ThreadedServer : BaseServer
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
	}
}
