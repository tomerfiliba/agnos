package agnos.packers;

import java.io.IOException;
import agnos.transports.ITransport;

public final class _Float extends AbstractPacker
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
	public void pack(Object obj, ITransport transport) throws IOException
	{
		if (obj == null) {
			pack(0.0, transport);
		}
		else {
			pack(((Number) obj).doubleValue(), transport);
		}
	}

	public void pack(double val, ITransport transport) throws IOException
	{
		Builtin.Int64.pack(Double.doubleToLongBits(val), transport);
	}

	@Override
	public Object unpack(ITransport transport) throws IOException
	{
		return new Double(Double.longBitsToDouble(((Long) (Builtin.Int64
				.unpack(transport))).longValue()));
	}
}
