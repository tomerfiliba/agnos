import java.util.*;
import java.io.*;
import agnos.*;
import RemoteFiles.RemoteFiles.*;
import RemoteFiles.Types.*;

public class myserver
{
	public static class MyFile implements IFile
	{
		protected String	_filename;

		// protected FileChannel fc;

		public MyFile(String filename, String mode) throws IOException
		{
			_filename = filename;
			/*
			 * if (mode == "r") { fc = FileChannel.open(new File(filename),
			 * READ); } else if (mode == "w") { fc = FileChannel.open(new
			 * File(filename), WRITE); } else { throw new
			 * UnderlyingIOError("invalid file open mode",
			 * RemoteFiles.Errno.EFAULT); }
			 */
		}

		public String get_filename() throws IOException,
				Protocol.ProtocolError, Protocol.PackedException,
				Protocol.GenericError
		{
			return _filename;
		}

		public StatRes stat() throws IOException, Protocol.ProtocolError,
				Protocol.PackedException, Protocol.GenericError
		{
			return new StatRes();
		}

		public byte[] read(Integer count) throws IOException,
				Protocol.ProtocolError, Protocol.PackedException,
				Protocol.GenericError
		{
			/*
			 * ByteBuffer bb = ByteBuffer.allocate(count); int size =
			 * fc.read(bb); return Arrays.copyOf(bb.array(), size);
			 */
			return null;
		}

		public void write(byte[] data) throws IOException,
				Protocol.ProtocolError, Protocol.PackedException,
				Protocol.GenericError
		{
			/*
			 * ByteBuffer bb = ByteBuffer.wrap(data); fc.write(bb);
			 */
		}

		public void close() throws IOException, Protocol.ProtocolError,
				Protocol.PackedException, Protocol.GenericError
		{
			// fc.close();
		}

		public void flush() throws IOException, Protocol.ProtocolError,
				Protocol.PackedException, Protocol.GenericError
		{
			// fc.force(false);
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
			Servers.SimpleServer server = new Servers.SimpleServer(new Processor(
					new MyHandler()), new Servers.SocketTransportFactory(17732));

			server.serve();
		} catch (Exception ex) {
			ex.printStackTrace();
		}
	}
}
