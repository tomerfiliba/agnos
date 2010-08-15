import java.util.*;
import filesystem.server_bindings.*;


public class myserver
{
	public static class File implements filesystem.IFile
	{
		protected String filename;
		protected filesystem.FileMode mode;
		protected Long pos;
		
		public File(String filename, filesystem.FileMode mode)
		{
			this.filename = filename;
			this.mode = mode;
			this.pos = new Long(0);
		}
		
		public byte[] read(Integer count) throws Exception
		{
			if ((mode.value & filesystem.FileMode.READ.value) == 0) {
				throw new Exception("not opened for reading");
			}
			byte[] buf = new byte[count];
			return buf;
		}

		public void write(byte[] data) throws Exception
		{
			if ((mode.value & filesystem.FileMode.WRITE.value) == 0) {
				throw new Exception("not opened for writing");
			}
			pos += data.length;
		}

		public void close() throws Exception
		{
		}

		public void seek(Long pos) throws Exception
		{
			this.pos = pos;
		}

		public Long tell() throws Exception
		{
			return pos;
		}
	}

	public static class Handler implements filesystem.IHandler
	{
		public filesystem.IFile open(String filename, filesystem.FileMode mode) throws Exception
		{
			return new File(filename, mode);
		}
	}

	public static void main(String[] args)
	{
		agnos.Servers.CmdlineServer server = new agnos.Servers.CmdlineServer(
				new filesystem.Processor(new Handler()));
		try {
			server.main(args);
		} catch (Exception ex) {
			ex.printStackTrace(System.out);
		}
	}

}
