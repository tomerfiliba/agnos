package agnos.packers;

import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;

public class _Float extends AbstractPacker
{
	protected _Float()
	{
	}

	@Override
	public int getId()
	{
		return 6;
	}
	
	@Override
	public void pack(Object obj, OutputStream stream) throws IOException
	{
		if (obj == null) {
			pack(0.0, stream);
		}
		else {
			pack(((Number) obj).doubleValue(), stream);
		}
	}

	public void pack(double val, OutputStream stream) throws IOException
	{
		Builtin.Int64.pack(Double.doubleToLongBits(val), stream);
	}

	@Override
	public Object unpack(InputStream stream) throws IOException
	{
		return new Double(Double.longBitsToDouble(((Long) (Builtin.Int64
				.unpack(stream))).longValue()));
	}
}
