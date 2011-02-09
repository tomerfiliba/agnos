package agnos.packers;

import java.io.IOException;
import agnos.transports.ITransport;


public final class _Bool extends AbstractPacker
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
	public void pack(Object obj, ITransport transport) throws IOException
	{
		if (obj == null) {
			pack(false, transport);
		}
		else {
			pack(((Boolean) obj).booleanValue(), transport);
		}
	}

	public void pack(boolean val, ITransport transport) throws IOException
	{
		Builtin.Int8.pack((byte)(val ? 1 : 0), transport);
	}

	@Override
	public Object unpack(ITransport transport) throws IOException
	{
		return new Boolean((((Byte) Builtin.Int8.unpack(transport))).byteValue() != 0);
	}
}
