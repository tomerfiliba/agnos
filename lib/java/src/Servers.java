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
			System.out.println("is bound = " + serverSocket.isBound());
			System.out.println("port = " + port + ", addr = " + addr);
		}
		
		public ITransport accept() throws IOException
		{
			System.out.println("accepting...");
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
	
	public abstract static class BaseServer
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
				System.out.println("goodbye");
			}
		}

		protected abstract void _handleClient(ITransport transport) throws Exception;
	}

	public static class SimpleServer extends BaseServer
	{
		public SimpleServer(Protocol.BaseProcessor processor, ITransportFactory transportFactory)
		{
			super(processor, transportFactory);
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
			catch (EOFException exc)
			{
				// finish on EOF
			}
			catch (SocketException exc)
			{
				System.out.println("!! SocketException: " + exc);
			}
		}
	}

	public static class ThreadedServer extends BaseServer
	{
		public ThreadedServer(Protocol.BaseProcessor processor, ITransportFactory transportFactory)
		{
			super(processor, transportFactory);
		}

		protected void _handleClient(ITransport transport) throws Exception
		{
			InputStream inStream = transport.getInputStream();
			OutputStream outStream = transport.getOutputStream();
		}
	}
	
	public abstract static class ChildServer
	{
		protected Process proc;
		public Protocol.BaseClient client;
		
		public ChildServer(ProcessBuilder procBuilder) throws IOException, UnknownHostException
		{
			Process p = procBuilder.start();
			InputStream stream = p.getInputStream();
			BufferedReader reader = new BufferedReader(new InputStreamReader(stream));
			String hostname = reader.readLine();
			String portstr = reader.readLine();
			stream.close();
			int port = Integer.parseInt(portstr);
			ITransport trans = new SocketTransport(hostname, port);
			client = getClient(trans);
		}
		
		protected abstract Protocol.BaseClient getClient(ITransport transport);
		
		public void close() throws IOException, InterruptedException
		{
			client.close();
			client = null;
			proc.waitFor();
		}
		
	}
}








