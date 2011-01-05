package agnos.packers;

import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;


public class _Bool extends AbstractPacker
{
	protected _Bool()
	{
	}

	@Override
	public int getId()
	{
		return 2;
	}

	@Override
	public void pack(Object obj, OutputStream stream) throws IOException
	{
		if (obj == null) {
			pack(false, stream);
		}
		else {
			pack(((Boolean) obj).booleanValue(), stream);
		}
	}

	public void pack(boolean val, OutputStream stream) throws IOException
	{
		Builtin.Int8.pack((byte)(val ? 1 : 0), stream);
	}

	@Override
	public Object unpack(InputStream stream) throws IOException
	{
		return new Boolean((((Byte) Builtin.Int8.unpack(stream))).byteValue() != 0);
	}
}
