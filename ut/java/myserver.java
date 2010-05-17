import java.util.*;
import java.io.*;
import RemoteFilesBindings.*;

public class myserver {
	public static class MyFile implements RemoteFilesBindings.IFile {
		protected String _filename;
		protected OutputStream fout;
		protected InputStream fin;

		public MyFile(String filename, String mode) throws Exception {
			_filename = filename;
			if (mode.equals("r")) {
				fin = new FileInputStream(filename);
			} else if (mode.equals("w")) {
				fout = new FileOutputStream(filename);
			} else {
				throw new RemoteFilesBindings.UnderlyingIOError(
						"invalid mode: " + mode,
						RemoteFilesBindings.Errno.EFAULT);
			}
		}

		public String get_filename() throws Exception {
			return _filename;
		}

		public RemoteFilesBindings.StatRes stat() throws Exception {
			return new RemoteFilesBindings.StatRes(new Integer(15),
					new Integer(12345), new Integer(17772), new Integer(1001),
					new Integer(1002), new Date(278346812),
					new Date(286621112), new Date(181775244));
		}

		public byte[] read(Integer count) throws Exception {
			byte[] buf = new byte[count];
			int size = fin.read(buf, 0, buf.length);
			if (size < 0) {
				size = 0; // eof - return empty array
			}
			return Arrays.copyOf(buf, size);
		}

		public void write(byte[] data) throws Exception {
			fout.write(data, 0, data.length);
		}

		public void close() throws Exception {
			if (fin != null) {
				fin.close();
			}
			if (fout != null) {
				fout.close();
			}
		}

		public void flush() throws Exception {
			throw new RemoteFilesBindings.UnderlyingIOError("cannot flush",
					RemoteFilesBindings.Errno.EFAULT);
		}
	}

	public static class MyHandler implements RemoteFilesBindings.IHandler {
		public void copy(RemoteFilesBindings.IFile src,
				RemoteFilesBindings.IFile dst) throws Exception {
			System.out.println("@copy: src= " + src + ", dst = " + dst);
			byte[] buf;
			while (true) {
				buf = src.read(10000);
				if (buf.length == 0)
					break;
				dst.write(buf);
			}
		}

		public RemoteFilesBindings.IFile open(String filename, String mode)
				throws Exception {
			System.out.println("@open: filename = '" + filename + "', mode = '"
					+ mode + "'");
			return new MyFile(filename, mode);
		}

		public List<String> pathToList(RemoteFilesBindings.IPath path,
				List<RemoteFilesBindings.IFile> spam,
				List<RemoteFilesBindings.IPath> bacon,
				List<RemoteFilesBindings.Moshe> eggs,
				List<RemoteFilesBindings.IPath> maps) throws Exception {
			List<String> arr = new ArrayList<String>();
			arr.add("hello");
			arr.add("world");
			return arr;
		}

	}

	public static void main(String[] args) {
		try {
			agnos.Servers.SimpleServer server = new agnos.Servers.SimpleServer(
					new RemoteFilesBindings.Processor(new MyHandler()),
					new agnos.Transports.SocketTransportFactory("localhost",
							17732));

			server.serve();
		} catch (Exception ex) {
			ex.printStackTrace();
		}
	}
}
