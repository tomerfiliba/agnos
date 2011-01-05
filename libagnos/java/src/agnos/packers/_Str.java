package agnos.packers;

import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;

public class _Str extends AbstractPacker
{
	private static final String encoding = "UTF-8";

	protected _Str()
	{
	}

	@Override
	public int getId()
	{
		return 9;
	}
	
	@Override
	public void pack(Object obj, OutputStream stream) throws IOException
	{
		if (obj == null) {
			Builtin.Buffer.pack(null, stream);
		}
		else {
			Builtin.Buffer.pack(((String) obj).getBytes(encoding), stream);
		}
	}

	@Override
	public Object unpack(InputStream stream) throws IOException
	{
		byte[] buf = (byte[]) Builtin.Buffer.unpack(stream);
		return new String(buf, encoding);
	}
}
