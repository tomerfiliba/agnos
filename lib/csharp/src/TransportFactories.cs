using System;
using System.IO;
using System.Net;
using System.Net.Sockets;


namespace Agnos.TransportFactories
{
	public interface ITransportFactory
	{
		Transports.ITransport Accept();
		void Close();
	}

	public class SocketTransportFactory : ITransportFactory
	{
		public TcpListener listener;

		public SocketTransportFactory(int port) :
			this(port, 10)
		{
		}

		public SocketTransportFactory(int port, int backlog) :
			this(IPAddress.Any, port, backlog)
		{
		}

		public SocketTransportFactory(String host, int port) :
			this(Dns.GetHostEntry(Dns.GetHostName()).AddressList[0], port, 10)
		{
		}

		public SocketTransportFactory(String host, int port, int backlog) :
			this(Dns.GetHostEntry(Dns.GetHostName()).AddressList[0], port, backlog)
		{
		}

		public SocketTransportFactory(IPAddress addr, int port, int backlog)
		{
			listener = new TcpListener(addr, port);
			listener.Start(backlog);
		}
		
		public ITransport Accept()
		{
			return new Transport.SocketTransport(listener.AcceptSocket());
		}
		
		public void Close()
		{
			listener.Stop();
		}
	}
	
}