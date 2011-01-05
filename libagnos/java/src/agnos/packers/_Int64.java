package agnos.packers;

import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;

public class _Int64 extends AbstractPacker
{
	private final byte[] buffer = new byte[8];

	protected _Int64()
	{
	}

	@Override
	public int getId()
	{
		return 5;
	}

	@Override
	public void pack(Object obj, OutputStream stream) throws IOException
	{
		if (obj == null) {
			pack((long) 0, stream);
		}
		else {
			pack(((Number) obj).longValue(), stream);
		}
	}

	public void pack(long val, OutputStream stream) throws IOException
	{
		buffer[0] = (byte) ((val >> 56) & 0xff);
		buffer[1] = (byte) ((val >> 48) & 0xff);
		buffer[2] = (byte) ((val >> 40) & 0xff);
		buffer[3] = (byte) ((val >> 32) & 0xff);
		buffer[4] = (byte) ((val >> 24) & 0xff);
		buffer[5] = (byte) ((val >> 16) & 0xff);
		buffer[6] = (byte) ((val >> 8) & 0xff);
		buffer[7] = (byte) (val & 0xff);
		_write(stream, buffer);
	}

	@Override
	public Object unpack(InputStream stream) throws IOException
	{
		_read(stream, buffer);

		return new Long(((long) (buffer[0] & 0xff) << 56)
				| ((long) (buffer[1] & 0xff) << 48)
				| ((long) (buffer[2] & 0xff) << 40)
				| ((long) (buffer[3] & 0xff) << 32)
				| ((long) (buffer[4] & 0xff) << 24)
				| ((long) (buffer[5] & 0xff) << 16)
				| ((long) (buffer[6] & 0xff) << 8)
				| (long) (buffer[7] & 0xff));
	}
}
