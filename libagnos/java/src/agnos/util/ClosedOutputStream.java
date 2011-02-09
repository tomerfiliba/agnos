import java.io.IOException;
import java.io.OutputStream;

public class ClosedOutputStream extends OutputStream
{
	private static ClosedOutputStream instance;
	
	private ClosedOutputStream() {
	}
	
	public static getInstance() {
		if (instance == null) {
			instance = new ClosedOutputStream();
		}
		return instance;
	}
	
	@Override
	public void write(int b) throws IOException {
		throw new IOException("closed stream");
	}
	
	@Override
	public void flush() throws IOException {
		throw new IOException("closed stream");
	}
}

