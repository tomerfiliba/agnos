import java.io.IOException;
import java.io.InputStream;

public class ClosedInputStream extends InputStream
{
	private static ClosedInputStream instance;
	
	private ClosedInputStream() {
	}
	
	public static getInstance() {
		if (instance == null) {
			instance = ClosedInputStream();
		}
		return instance;
	}
	
	@Override
	public int read() throws IOException {
		throw new IOException("closed stream");
	}
}

