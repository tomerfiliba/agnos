package agnos;

import java.io.*;
import java.util.*;
import java.net.*;


public class TransportFactories
{
	public interface ITransportFactory 
	{
		void close() throws IOException;
		Transports.ITransport accept() throws IOException;
	}
	
	public static class SocketTransportFactory implements ITransportFactory 
	{
		protected int backlog;
		protected ServerSocket serverSocket;

		public SocketTransportFactory(int port) throws IOException {
			this(port, 10);
		}

		public SocketTransportFactory(int port, int backlog) throws IOException {
			this(InetAddress.getLocalHost(), port, backlog);
		}

		public SocketTransportFactory(String host, int port) throws IOException {
			this(host, port, 10);
		}

		public SocketTransportFactory(String host, int port, int backlog) throws IOException {
			this(InetAddress.getByName(host), port, backlog);
		}

		public SocketTransportFactory(InetAddress addr, int port, int backlog)
				throws IOException {
			serverSocket = new ServerSocket(port, backlog, addr);
			this.backlog = backlog;
		}

		public void close() throws IOException {
			serverSocket.close();
		}

		public Transports.ITransport accept() throws IOException {
			return new Transports.SocketTransport(serverSocket.accept());
		}
	}
	
}