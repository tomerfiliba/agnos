package agnos.packers;

import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;

public class _Int16 extends AbstractPacker
{
	private byte[] buffer = new byte[2];

	protected _Int16()
	{
	}

	@Override
	public int getId()
	{
		return 3;
	}

	@Override
	public void pack(Object obj, OutputStream stream) throws IOException
	{
		if (obj == null) {
			pack((short) 0, stream);
		}
		else {
			pack(((Number) obj).shortValue(), stream);
		}
	}

	public void pack(short val, OutputStream stream) throws IOException
	{
		buffer[0] = (byte) ((val >> 8) & 0xff);
		buffer[1] = (byte) (val & 0xff);
		_write(stream, buffer);
	}

	@Override
	public Object unpack(InputStream stream) throws IOException
	{
		_read(stream, buffer);
		return new Short(
				(short) (((buffer[0] & 0xff) << 8) | (buffer[1] & 0xff)));
	}
}
