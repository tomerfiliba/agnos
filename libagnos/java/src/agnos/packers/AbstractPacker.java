package agnos.packers;

import java.io.EOFException;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;

import agnos.transports.ITransport;


public abstract class AbstractPacker
{
	abstract public void pack(Object obj, OutputStream stream)
			throws IOException;

	abstract public Object unpack(InputStream stream) throws IOException;

	abstract public int getId();

	public void pack(Object obj, ITransport transport)
			throws IOException
	{
		pack(obj, transport.getOutputStream());
	}

	public Object unpack(ITransport transport)
			throws IOException
	{
		return unpack(transport.getInputStream());
	}

	protected static void _write(OutputStream stream, byte[] buffer)
			throws IOException
	{
		stream.write(buffer, 0, buffer.length);
	}

	protected static void _read(InputStream stream, byte[] buffer)
			throws IOException
	{
		int total_got = 0;
		int got;

		while (total_got < buffer.length) {
			got = stream.read(buffer, total_got, buffer.length - total_got);
			total_got += got;
			if (got <= 0 && total_got < buffer.length) {
				throw new EOFException("premature end of stream detected");
			}
		}
	}

}