package agnos;

import java.io.*;
import java.util.*;
import java.net.*;

public class Servers
{
	public abstract static class BaseServer
	{
		protected Protocol.BaseProcessor processor;
		protected Transports.ITransportFactory transportFactory;
		
		public BaseServer(Protocol.BaseProcessor processor, Transports.ITransportFactory transportFactory)
		{
			this.processor = processor;
			this.transportFactory = transportFactory;
		}
		
		public void serve() throws Exception
		{
			while (true)
			{
				Transports.ITransport transport = transportFactory.accept();
				acceptClient(transport);
			}
		}

		protected abstract void acceptClient(Transports.ITransport transport) throws Exception;
		
		protected static void serveClient(Protocol.BaseProcessor processor, Transports.ITransport transport) throws Exception
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

	public static class SimpleServer extends BaseServer
	{
		public SimpleServer(Protocol.BaseProcessor processor, Transports.ITransportFactory transportFactory)
		{
			super(processor, transportFactory);
		}

		protected void acceptClient(Transports.ITransport transport) throws Exception
		{
			serveClient(processor, transport);
		}
	}

	public static class ThreadedServer extends BaseServer
	{
		protected static class ThreadProc extends Thread 
		{
			protected Protocol.BaseProcessor processor;
			protected Transports.ITransport transport;
			
			ThreadProc(Protocol.BaseProcessor processor, Transports.ITransport transport)
			{
				this.processor = processor;
				this.transport = transport;
	        }

	        public void run()
	        {
	        	try {
		        	BaseServer.serveClient(processor, transport);
	        	}
	        	catch (Exception ex)
	        	{
	        		// should log this somehow
	        	}
	        }
	    }
		
		public ThreadedServer(Protocol.BaseProcessor processor, Transports.ITransportFactory transportFactory)
		{
			super(processor, transportFactory);
		}

		protected void acceptClient(Transports.ITransport transport) throws Exception
		{
			Thread t = new ThreadProc(processor, transport);
			t.start();
		}
	}

    public static class LibraryModeServer
    {
        protected ServerSocket serverSocket;
        protected Protocol.BaseProcessor processor;

        public LibraryModeServer(Protocol.BaseProcessor processor) throws IOException, UnknownHostException
        {
        	this(processor, InetAddress.getByName("127.0.0.1"));
        }

        public LibraryModeServer(Protocol.BaseProcessor processor, InetAddress addr) throws IOException
        {
            this.processor = processor;
            serverSocket = new ServerSocket(0, 1, addr);
        }

        public void serve() throws Exception
        {
            System.out.println(serverSocket.getInetAddress().toString());
            System.out.println(serverSocket.getLocalPort());
            System.out.flush();
            System.out.close();
            
            Transports.ITransport transport = new Transports.SocketTransport(serverSocket.accept());
            serverSocket.close();
            BaseServer.serveClient(processor, transport);
        }
    }	
	
}








