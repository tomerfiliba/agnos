import java.util.*;
import java.io.*;
//import agnos.*;
import RemoteFiles.Service.*;
import RemoteFiles.Types.*;

public class myserver
{
	public static class MyFile implements IFile
	{
		protected String	_filename;

		// protected FileChannel fc;

		public MyFile(String filename, String mode) throws Exception
		{
			_filename = filename;
			if (mode != "r" && mode != "w") {
				throw new UnderlyingIOError("invalid file open mode",
						Errno.EFAULT);

			}
		}

		public String get_filename() throws Exception
		{
			return _filename;
		}

		public StatRes stat() throws Exception
		{
			return new StatRes(new Integer(15), new Integer(12345),
					new Integer(17772), new Integer(1001), new Integer(1002),
					new Date(), new Date(), new Date());
		}

		public byte[] read(Integer count) throws Exception
		{
			byte[] buf = new byte[] { 1, 2, 3, 4, 5, 6 };
			return buf;
		}

		public void write(byte[] data) throws Exception
		{
			System.out.println("#write");
		}

		public void close() throws Exception
		{
			System.out.println("#close");
		}

		public void flush() throws Exception
		{
			System.out.println("#flush");
		}
	}

	public static class MyHandler implements IHandler
	{
		public void copy(IFile src, IFile dst) throws Exception
		{
			byte[] buf;
			while (true) {
				buf = src.read(10000);
				if (buf.length == 0)
					break;
				dst.write(buf);
			}
			dst.flush();
		}

		public IFile open(String filename, String mode) throws Exception
		{
			return new MyFile(filename, mode);
		}
	}

	public static void main(String[] args)
	{
		try {
			agnos.Servers.SimpleServer server = new agnos.Servers.SimpleServer(
					new Processor(new MyHandler()),
					new agnos.Servers.SocketTransportFactory("localhost", 17732));

			System.out.println("starting server");
			server.serve();
		} catch (Exception ex) {
			ex.printStackTrace();
		}
	}
}
