package agnos;

import java.io.*;
import java.util.*;
import java.net.*;
import static agnos.Protocol.IProcessorFactory;
import static agnos.Protocol.BaseProcessor;
import static agnos.Transports.ITransport;
import static agnos.TransportFactories.ITransportFactory;
import static agnos.TransportFactories.SocketTransportFactory;


public class Servers
{
	public abstract static class BaseServer
	{
		protected IProcessorFactory processorFactory;
		protected ITransportFactory transportFactory;

		public BaseServer(IProcessorFactory processorFactory,
				ITransportFactory transportFactory)
		{
			this.processorFactory = processorFactory;
			this.transportFactory = transportFactory;
		}

		public void serve() throws Exception
		{
			while (true) {
				// System.err.println("accepting...");
				ITransport transport = transportFactory.accept();
				BaseProcessor processor = processorFactory.create(transport);
				serveClient(processor);
			}
		}

		protected abstract void serveClient(BaseProcessor processor) throws Exception;

		protected static void _serveClient(BaseProcessor processor) throws Exception
		{
			try {
				while (true) {
					processor.process();
				}
			} catch (EOFException exc) {
				// finish on EOF
			} catch (SocketException exc) {
				// System.out.println("!! SocketException: " + exc);
			} finally {
				processor.transport.close();
			}
		}
	}

	public static class SimpleServer extends BaseServer
	{
		public SimpleServer(IProcessorFactory processorFactory,
				ITransportFactory transportFactory)
		{
			super(processorFactory, transportFactory);
		}

		protected void serveClient(BaseProcessor processor) throws Exception
		{
			_serveClient(processor);
		}
	}

	public static class ThreadedServer extends BaseServer
	{
		protected static class ThreadProc extends Thread
		{
			protected BaseProcessor processor;

			ThreadProc(BaseProcessor processor)
			{
				this.processor = processor;
			}

			public void run()
			{
				try {
					BaseServer._serveClient(processor);
				} catch (Exception ex) {
					// should log this somehow
				}
			}
		}

		public ThreadedServer(IProcessorFactory processorFactory,
				ITransportFactory transportFactory)
		{
			super(processorFactory, transportFactory);
		}

		protected void serveClient(BaseProcessor processor) throws Exception
		{
			Thread t = new ThreadProc(processor);
			t.start();
		}
	}

	public static class LibraryModeServer extends BaseServer
	{
		public LibraryModeServer(IProcessorFactory processorFactory)
				throws IOException, UnknownHostException
		{
			this(processorFactory, new SocketTransportFactory("127.0.0.1", 0));
		}

		public LibraryModeServer(IProcessorFactory processorFactory,
				SocketTransportFactory transportFactory)
				throws IOException
		{
			super(processorFactory, transportFactory);
		}

		public void serve() throws Exception
		{
			ServerSocket serverSocket = ((SocketTransportFactory) transportFactory).serverSocket;
			System.out.println("AGNOS");
			System.out.println(serverSocket.getInetAddress().getHostAddress());
			System.out.println(serverSocket.getLocalPort());
			System.out.flush();
			System.out.close();

			ITransport transport = transportFactory.accept();
			transportFactory.close();
			BaseProcessor processor = processorFactory.create(transport);
			_serveClient(processor);
		}

		protected void serveClient(BaseProcessor processor) throws Exception
		{
			throw new AssertionError("should never be called");
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
		protected IProcessorFactory processorFactory;

		protected static enum ServingMode
		{
			SIMPLE, THREADED, LIB
		}

		public CmdlineServer(IProcessorFactory processorFactory)
		{
			this.processorFactory = processorFactory;
		}

		public void main(String[] args) throws Exception
		{
			ServingMode mode = ServingMode.SIMPLE;
			String host = "127.0.0.1";
			int port = 0;

			for (int i = 0; i < args.length; i += 1) {
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

			switch (mode) {
			case SIMPLE:
				if (port == 0) {
					throw new SwitchException(
							"simple server requires specifying a port");
				}
				server = new SimpleServer(processorFactory, 
						new SocketTransportFactory(host, port));
				break;
			case THREADED:
				if (port == 0) {
					throw new SwitchException(
							"threaded server requires specifying a port");
				}
				server = new ThreadedServer(processorFactory,
						new SocketTransportFactory(host, port));
				break;
			case LIB:
				server = new LibraryModeServer(processorFactory,
						new SocketTransportFactory(host, port));
				break;
			default:
				throw new SwitchException("invalid mode: " + mode);
			}

			server.serve();
		}
	}

}
