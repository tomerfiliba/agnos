package agnos;

import java.io.*;
import java.util.*;
import java.net.*;

public class Transports
{
	public interface ITransportFactory
	{
		ITransport accept() throws IOException;
		void close() throws IOException;
	}

	public interface ITransport
	{
		InputStream getInputStream() throws IOException;
		OutputStream getOutputStream() throws IOException;
	}
	
	public static class SocketTransportFactory implements ITransportFactory
	{
		public static final int backlog = 10;
		public ServerSocket serverSocket;

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
		
		public void close() throws IOException
		{
			serverSocket.close();
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
	
    public static class ProcTransport implements ITransport
    {
        public Process proc;
        public ITransport transport;

        public ProcTransport(Process proc, ITransport transport)
        {
            this.proc = proc;
            this.transport = transport;
        }

        public InputStream getInputStream() throws IOException
        {
            return transport.getInputStream();
        }
        
        public OutputStream getOutputStream() throws IOException
        {
            return transport.getOutputStream();
        }

        public static ProcTransport connect(String filename) throws Exception
        {
            return connect(filename, "-m", "lib");
        }

        public static ProcTransport connect(String filename, String... args) throws Exception 
        {
        	ArrayList<String> cmdline = new ArrayList<String>();
        	cmdline.add(filename);
        	cmdline.addAll(Arrays.asList(args));
        	ProcessBuilder pb = new ProcessBuilder(cmdline);
        	pb.redirectErrorStream(true);
            return connect(pb);
        }

        public static ProcTransport connect(ProcessBuilder procbuilder) throws Exception
        {
        	Process proc = procbuilder.start();
        	BufferedReader reader = new BufferedReader(new InputStreamReader(
                    new BufferedInputStream(proc.getInputStream())));
        	String hostname = reader.readLine();
            int port = Integer.parseInt(reader.readLine());
            
            ITransport transport = new SocketTransport(hostname, port);
            return new ProcTransport(proc, transport);
        }
    }
}








