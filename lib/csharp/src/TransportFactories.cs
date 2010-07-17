using System;
using System.IO;
using System.Net;
using System.Net.Sockets;
using Agnos.Transports;


namespace Agnos.TransportFactories
{
	public interface ITransportFactory
	{
		Transports.ITransport Accept();
		void Close();
	}

	public class SocketTransportFactory : ITransportFactory
	{
		internal TcpListener listener;
        public const int DefaultBacklog = 10;

		public SocketTransportFactory(int port) :
			this(IPAddress.Any, port)
		{
		}

		public SocketTransportFactory(int port, int backlog) :
			this(IPAddress.Any, port, backlog)
		{
		}

        protected static IPAddress GetIPv4AddressOf(String host)
        {
            foreach (IPAddress addr in Dns.GetHostEntry(host).AddressList) {
                if (addr.AddressFamily == AddressFamily.InterNetwork) {
                    return addr;
                }
            }
            return null;
        }

		public SocketTransportFactory(String host, int port) :
            this(GetIPv4AddressOf(host), port)
		{
		}

		public SocketTransportFactory(String host, int port, int backlog) :
            this(GetIPv4AddressOf(host), port, backlog)
		{
		}

        public SocketTransportFactory(IPAddress addr, int port) :
            this(addr, port, DefaultBacklog)
        {
        }

        public SocketTransportFactory(IPAddress addr, int port, int backlog)
        {
            listener = new TcpListener(addr, port);
            listener.Start(backlog);
        }

		public ITransport Accept()
		{
			return new SocketTransport(listener.AcceptSocket());
		}
		
		public void Close()
		{
			listener.Stop();
		}
	}
	
}