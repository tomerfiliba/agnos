package agnos.packers;

import java.io.EOFException;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;

import agnos.transports.ITransport;


public abstract class AbstractPacker
{
	abstract public void pack(Object obj, ITransport transport)
			throws IOException;

	abstract public Object unpack(ITransport transport) throws IOException;

	abstract public int getId();

	protected static void _write(ITransport transport, byte[] buffer)
			throws IOException
	{
		transport.write(buffer, 0, buffer.length);
	}

	protected static void _read(ITransport transport, byte[] buffer)
			throws IOException
	{
		int total_got = 0;
		int got;

		while (total_got < buffer.length) {
			got = transport.read(buffer, total_got, buffer.length - total_got);
			total_got += got;
			if (got <= 0 && total_got < buffer.length) {
				throw new EOFException("premature end of stream detected");
			}
		}
	}

}