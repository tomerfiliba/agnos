package agnos.packers;

import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;


public class _Int8 extends AbstractPacker
{
	private byte[] buffer = new byte[1];

	protected _Int8()
	{
	}

	@Override
	public int getId()
	{
		return 1;
	}
	
	@Override
	public void pack(Object obj, OutputStream stream) throws IOException
	{
		if (obj == null) {
			pack((byte) 0, stream);
		}
		else {
			pack(((Number) obj).byteValue(), stream);
		}
	}

	public void pack(byte val, OutputStream stream) throws IOException
	{
		buffer[0] = val;
		_write(stream, buffer);
	}

	@Override
	public Object unpack(InputStream stream) throws IOException
	{
		_read(stream, buffer);
		return new Byte(buffer[0]);
	}
}