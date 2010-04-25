using System;
using System.IO;
using System.Net;
using System.Net.Sockets;


namespace Agnos.Transports
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
			listener.Start(backlog);
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
		
		public SocketTransport(String host, int port)
		{
			sock = new Socket(AddressFamily.InterNetwork, SocketType.Stream, ProtocolType.Tcp);
			sock.Connect(host, port);
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
}