package agnos.packers;

import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;

public class _Buffer extends AbstractPacker
{
	protected _Buffer()
	{
	}

	@Override
	public int getId()
	{
		return 7;
	}
	
	@Override
	public void pack(Object obj, OutputStream stream) throws IOException
	{
		if (obj == null) {
			Builtin.Int32.pack(0, stream);
		}
		else {
			byte[] val = (byte[]) obj;
			Builtin.Int32.pack(val.length, stream);
			_write(stream, val);
		}
	}

	@Override
	public Object unpack(InputStream stream) throws IOException
	{
		int length = (Integer) Builtin.Int32.unpack(stream);
		byte[] buf = new byte[length];
		_read(stream, buf);
		return buf;
	}
}
