using System;
using System.IO;
using System.Net;
using Agnos;
using RemoteFilesBindings;
using System.Collections.Generic;


namespace server_test
{
	public class MyFile : RemoteFiles.IFile
	{
		protected String	_filename;
		protected BinaryWriter fout;
		protected BinaryReader fin;

		public MyFile(String filename, string mode)
		{
			_filename = filename;
			if (mode == "r") {
				fin = new BinaryReader(File.Open(filename, FileMode.Open));
			}
			else if (mode == "w") {
				fout = new BinaryWriter(File.Open(filename, FileMode.Create));
			}
			else {
				throw new RemoteFiles.UnderlyingIOError("invalid mode: " + mode, RemoteFiles.Errno.EFAULT);
			}
		}

		public String filename
		{
			get
			{
				return _filename;
			}
		}

		public RemoteFiles.StatRes stat()
		{
			return new RemoteFiles.StatRes(15, 12345, 17772, 1001, 1002, DateTime.Now, DateTime.Now, DateTime.Now);
		}

		public byte[] read(int count)
		{
			byte[] buf = new byte[count];
			int size = fin.Read(buf, 0, buf.Length);			
			if (size < 0) {
				size = 0; // eof - return empty array
			}
			byte[] output = new byte[size];
			System.Array.Copy(buf, output, size);
			return output;
		}

		public void write(byte[] data)
		{
			fout.Write(data, 0, data.Length);
		}

		public void close()
		{
			if (fin != null) {
				fin.Close();
			}
			if (fout != null) {
				fout.Close();
			}
		}

		public void flush()
		{
			throw new RemoteFiles.UnderlyingIOError("cannot flush", RemoteFiles.Errno.EFAULT);
		}
	}

	public class MyHandler : RemoteFiles.IHandler
	{
		public void copy(RemoteFiles.IFile src, RemoteFiles.IFile dst)
		{
			System.Console.WriteLine("@copy: src= {0}, dst = {1}", src, dst);
			byte[] buf;
			while (true) {
				buf = src.read(10000);
				if (buf.Length == 0)
					break;
				dst.write(buf);
			}
		}

		public RemoteFiles.IFile open(String filename, String mode)
		{
			System.Console.WriteLine("@open: filename = {0}, mode={1}", filename, mode);
			return new MyFile(filename, mode);
		}
		
        public List<string> pathToList(RemoteFiles.IPath path, List<RemoteFiles.IFile> spam, List<RemoteFiles.IPath> bacon, List<RemoteFiles.Moshe> eggs, List<RemoteFiles.IPath> maps)
		{
			return new List<string> {"hello", "world"};
		}
	}

	public class MainClass
	{
		public static void Main(string[] args)
		{
			Agnos.Servers.SimpleServer server = new Agnos.Servers.SimpleServer(
					new RemoteFiles.Processor(new MyHandler()),
					new Agnos.Transports.SocketTransportFactory(IPAddress.Loopback, 17735));

			server.serve();
		}
	}
}

