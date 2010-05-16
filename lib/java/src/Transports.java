package agnos;

import java.io.*;
import java.util.*;
import java.net.*;

public class Transports
{
	public interface ITransportFactory
	{
		ITransport accept() throws IOException;
	}

	public interface ITransport
	{
		InputStream getInputStream() throws IOException;
		OutputStream getOutputStream() throws IOException;
	}
	
	public static class SocketTransportFactory implements ITransportFactory
	{
		public static final int backlog = 10;
		protected ServerSocket serverSocket;

		public SocketTransportFactory(int port) throws IOException
		{
			this(InetAddress.getLocalHost(), port);
		}

		public SocketTransportFactory(String host, int port) throws IOException
		{
			this(InetAddress.getByName(host), port);
		}

		public SocketTransportFactory(InetAddress addr, int port) throws IOException
		{
			serverSocket = new ServerSocket(port, backlog, addr);
		}
		
		public ITransport accept() throws IOException
		{
			return new SocketTransport(serverSocket.accept());
		}
	}
	
	public static class SocketTransport implements ITransport
	{
		protected Socket sock;
		public static final int bufsize = 8000;
		
		public SocketTransport(Socket sock)
		{
			this.sock = sock;
		}
		
		public SocketTransport(String host, int port) throws IOException, UnknownHostException
		{
			this(new Socket(host, port));
		}
		
		public InputStream getInputStream() throws IOException
		{
			return new BufferedInputStream(sock.getInputStream(), bufsize);
		}

		public OutputStream getOutputStream() throws IOException
		{
			return new BufferedOutputStream(sock.getOutputStream(), bufsize);
		}
	}
	
}








