package agnos;

import java.io.*;
import java.util.*;
import java.net.*;


public class Servers
{
	public abstract static class BaseServer
	{
		protected Protocol.BaseProcessor processor;
		protected TransportFactories.ITransportFactory transportFactory;
		
		public BaseServer(Protocol.BaseProcessor processor, TransportFactories.ITransportFactory transportFactory)
		{
			this.processor = processor;
			this.transportFactory = transportFactory;
		}
		
		public void serve() throws Exception
		{
			while (true)
			{
				//System.err.println("accepting...");
				Transports.ITransport transport = transportFactory.accept();
				acceptClient(transport);
			}
		}

		protected abstract void acceptClient(Transports.ITransport transport) throws Exception;
		
		protected static void serveClient(Protocol.BaseProcessor processor, Transports.ITransport transport) throws Exception
		{
			try
			{
				//processor.handshake(inStream, outStream);
				while (true)
				{
					processor.process(transport);
				}
			}
			catch (EOFException exc)
			{
				// finish on EOF
			}
			catch (SocketException exc)
			{
				//System.out.println("!! SocketException: " + exc);
			}
			finally 
			{
				transport.close();
			}
		}
	}

	public static class SimpleServer extends BaseServer
	{
		public SimpleServer(Protocol.BaseProcessor processor, TransportFactories.ITransportFactory transportFactory)
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
		
		public ThreadedServer(Protocol.BaseProcessor processor, TransportFactories.ITransportFactory transportFactory)
		{
			super(processor, transportFactory);
		}

		protected void acceptClient(Transports.ITransport transport) throws Exception
		{
			Thread t = new ThreadProc(processor, transport);
			t.start();
		}
	}

    public static class LibraryModeServer extends BaseServer
    {
        public LibraryModeServer(Protocol.BaseProcessor processor) throws IOException, UnknownHostException
        {
        		this(processor, new TransportFactories.SocketTransportFactory("127.0.0.1", 0));
        }

        public LibraryModeServer(Protocol.BaseProcessor processor, TransportFactories.SocketTransportFactory transportFactory) throws IOException
        {
        		super(processor, transportFactory);
        }

        public void serve() throws Exception
        {
        		ServerSocket serverSocket = ((TransportFactories.SocketTransportFactory)transportFactory).serverSocket;
        		System.out.println("AGNOS");
            System.out.println(serverSocket.getInetAddress().getHostAddress());
            System.out.println(serverSocket.getLocalPort());
            System.out.flush();
            System.out.close();
            
            Transports.ITransport transport = transportFactory.accept();
            transportFactory.close();
            serveClient(processor, transport);
        }

		protected void acceptClient(Transports.ITransport transport) throws Exception
		{
		}
    }
    
    public static class SwitchException extends Exception
    {
    		public SwitchException(String message)
    		{
    			super(message);
    		}
    }

	public static class CmdlineServer
	{
		protected Protocol.BaseProcessor processor;
		
		protected static enum ServingMode
		{
			SIMPLE,
			THREADED,
			LIB
		}
		
		public CmdlineServer(Protocol.BaseProcessor processor)
		{
			this.processor = processor;
		}
		
		public void main(String[] args) throws Exception
		{
			ServingMode mode = ServingMode.SIMPLE;
			String host = "127.0.0.1";
			int port = 0;
			
			for(int i = 0; i < args.length; i += 1)
			{
				String arg = args[i];
				if (arg.equals("-m")) {
					i += 1;
					if (i >= args.length) {
						throw new SwitchException("-m requires an argument");
					}
					arg = args[i].toLowerCase();
					if (arg.equals("lib") || arg.equals("library")) {
						mode = ServingMode.LIB;
					}
					else if (arg.equals("simple")) {
						mode = ServingMode.SIMPLE;
					}
					else if (arg.equals("threaded")) {
						mode = ServingMode.THREADED;
					}
					else {
						throw new SwitchException("invalid mode: " + arg);
					}
				}
				else if (arg.equals("-h")) {
					i += 1;
					if (i >= args.length) {
						throw new SwitchException("-h requires an argument");
					}
					host = args[i];
				}
				else if (arg.equals("-p")) {
					i += 1;
					if (i >= args.length) {
						throw new SwitchException("-p requires an argument");
					}
					port = Integer.parseInt(args[i]);					
				}
				else {
					throw new SwitchException("invalid switch: " + arg);
				}
			}
			
			BaseServer server = null;
			
			switch (mode)
			{
			case SIMPLE:
				if (port == 0) {
					throw new SwitchException("simple server requires specifying a port");
				}
				server = new SimpleServer(processor, new TransportFactories.SocketTransportFactory(host, port));
				break;
			case THREADED:
				if (port == 0) {
					throw new SwitchException("threaded server requires specifying a port");
				}
				server = new ThreadedServer(processor, new TransportFactories.SocketTransportFactory(host, port));
				break;
			case LIB:
				server = new LibraryModeServer(processor, new TransportFactories.SocketTransportFactory(host, port));
				break;
			default:
				throw new SwitchException("invalid mode: " + mode);
			}
			
			server.serve();
		}
	}
    
}








