package agnos.util;

import java.io.IOException;
import java.io.InputStream;

public class ClosedInputStream extends InputStream
{
	private static ClosedInputStream instance;
	
	private ClosedInputStream() {
	}
	
	public static ClosedInputStream getInstance() {
		if (instance == null) {
			instance = new ClosedInputStream();
		}
		return instance;
	}
	
	@Override
	public int read() throws IOException {
		throw new IOException("closed stream");
	}
}

