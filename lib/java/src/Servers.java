package agnos;

import java.io.*;
import java.util.*;
import java.net.*;

public class Servers
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
		public static final int bufsize = 4096;
		
		public SocketTransport(Socket sock)
		{
			this.sock = sock;
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
	
	public static class BaseServer
	{
		Protocol.BaseProcessor processor;
		ITransportFactory transportFactory;
		
		public BaseServer(Protocol.BaseProcessor processor, ITransportFactory transportFactory)
		{
			this.processor = processor;
			this.transportFactory = transportFactory;
		}
		
		public void serve() throws Exception
		{
			while (true)
			{
				ITransport transport = transportFactory.accept();
				_handleClient(transport);
			}
		}
		
		protected void _handleClient(ITransport transport) throws Exception
		{
			InputStream inStream = transport.getInputStream();
			OutputStream outStream = transport.getOutputStream();
			
			try
			{
				while (true)
				{
					processor.process(inStream, outStream);
				}
			}
			catch (IOException exc)
			{
				// check for EOF
			}
		}
	}

	public static class SimpleServer extends BaseServer
	{
		public SimpleServer(Protocol.BaseProcessor processor, ITransportFactory transportFactory)
		{
			super(processor, transportFactory);
		}
	}

	public static class ThreadedServer extends BaseServer
	{
		public ThreadedServer(Protocol.BaseProcessor processor, ITransportFactory transportFactory)
		{
			super(processor, transportFactory);
		}
	}
		
}