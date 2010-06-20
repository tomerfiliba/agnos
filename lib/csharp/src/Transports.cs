using System;
using System.IO;
using System.Net;
using System.Net.Sockets;
using System.Diagnostics;


namespace Agnos.Transports
{
	public interface ITransport
	{
		Stream getInputStream();
		Stream getOutputStream();
	}

	public interface ITransportFactory
	{
		ITransport Accept();
		void Close();
	}

	public class SocketTransportFactory : ITransportFactory
	{
		public const int backlog = 10;
		public TcpListener listener;

		public SocketTransportFactory(int port) :
			this(IPAddress.Any, port)
		{
		}

		public SocketTransportFactory(String host, int port) :
			this(Dns.GetHostEntry(Dns.GetHostName()).AddressList[0], port)
		{
		}

		public SocketTransportFactory(IPAddress addr, int port)
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
	
	public class SocketTransport : ITransport
	{
		protected Socket sock;
		public const int bufsize = 8000;
		
		public SocketTransport(Socket sock)
		{
			this.sock = sock;
		}
		
		public SocketTransport(String host, int port)
		{
			sock = new Socket(AddressFamily.InterNetwork, SocketType.Stream, ProtocolType.Tcp);
			sock.Connect(host, port);
		}

		public SocketTransport(IPAddress addr, int port)
		{
			sock = new Socket(addr.AddressFamily, SocketType.Stream, ProtocolType.Tcp);
			sock.Connect(addr, port);
		}
		
		public Stream getInputStream()
		{
			return new BufferedStream(new NetworkStream(sock), bufsize);
		}

		public Stream getOutputStream()
		{
			return new BufferedStream(new NetworkStream(sock), bufsize);
		}
	}
	
    public class ProcTransport : ITransport
    {
        public Process proc;
        public ITransport transport;

        public ProcTransport(Process proc, ITransport transport)
        {
            this.proc = proc;
            this.transport = transport;
        }

        public Stream getInputStream()
        {
            return transport.getInputStream();
        }

        public Stream getOutputStream()
        {
            return transport.getOutputStream();
        }

        public static ProcTransport connect(string filename)
        {
            return connect(filename, "-m lib");
        }

        public static ProcTransport connect(string filename, string args)
        {
            Process proc = new Process();
            proc.StartInfo.UseShellExecute = false;
            proc.StartInfo.FileName = filename;
            proc.StartInfo.Arguments = args;
            proc.StartInfo.CreateNoWindow = true;
            proc.StartInfo.RedirectStandardInput = true;
            proc.StartInfo.RedirectStandardOutput = true;
            proc.StartInfo.RedirectStandardError = true;
            return connect(proc);
        }

        public static ProcTransport connect(Process proc)
        {
            proc.Start();
            string hostname = proc.StandardOutput.ReadLine();
            int port = Int16.Parse(proc.StandardOutput.ReadLine());
            ITransport transport = new SocketTransport(hostname, port);
            return new ProcTransport(proc, transport);
        }
    }
}