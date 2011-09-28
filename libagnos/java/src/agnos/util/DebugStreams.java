package agnos.util;

import java.io.OutputStream;
import java.io.InputStream;
import java.io.IOException;
import java.util.logging.Logger;

public class DebugStreams
{
	protected static String hexify(byte[] data, int off, int len)
	{
		StringBuffer sb = new StringBuffer(data.length * 2);
		for (int i = off; i < len; i++) {
			sb.append(String.format("%02x ", data[i]));
		}
		return sb.toString();
	}

	public static class LoggingOutputStream extends OutputStream
	{
		protected OutputStream underlying;
		protected Logger logger;
		
		public LoggingOutputStream(Logger logger, OutputStream underlying)
		{
			this.logger = logger;
			this.underlying = underlying;
		}

		@Override 
		public void flush() throws IOException
		{
			logger.info("flush");
			underlying.flush();
		}

		@Override 
		public void write(int b) throws IOException
		{
			write(new byte[]{(byte)b});
		}
		@Override 
		public void write(byte[] data) throws IOException
		{
			write(data, 0, data.length);
		}
		@Override 
		public void write(byte[] data, int off, int len) throws IOException
		{
			logger.info(String.format("W (%d) %s", len - off, hexify(data, off, len)));
			underlying.write(data, off, len);
			logger.info("-W    OK");
		}
		@Override
		public void close() throws IOException
		{
			underlying.close();
		}	
	}
	
	public static class LoggingInputStream extends InputStream
	{
		protected InputStream underlying;
		protected Logger logger;
		
		public LoggingInputStream(Logger logger, InputStream underlying)
		{
			this.logger = logger;
			this.underlying = underlying;
		}

		@Override
		public int read() throws IOException
		{
			byte[] buffer = { 0 };
			if (read(buffer) < 0) {
				return -1;
			}
			return buffer[0];
		}
		@Override
		public int read(byte[] data) throws IOException
		{
			return read(data, 0, data.length);
		}
		@Override
		public int read(byte[] data, int off, int len) throws IOException
		{
			logger.info(String.format("R (%d)", len - off));
			int count = underlying.read(data, off, len);
			if (count < 0) {
				logger.info("-R    <EOF>");
			}
			else {
				logger.info("-R    " + hexify(data, off, count));
			}
			return count;
		}
		@Override
		public long skip(long n) throws IOException 
		{
			logger.info(String.format("SKIP (%d)", n));
			return underlying.skip(n);
		}
		@Override
		public void close() throws IOException
		{
			underlying.close();
		}
		@Override
		public int available() throws IOException
		{
			return underlying.available();
		}
		
	};
	
	
}



