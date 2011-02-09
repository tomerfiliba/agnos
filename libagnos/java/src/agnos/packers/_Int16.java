package agnos.packers;

import java.io.IOException;
import agnos.transports.ITransport;

public final class _Int16 extends AbstractPacker
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
	public void pack(Object obj, ITransport transport) throws IOException
	{
		if (obj == null) {
			pack((short) 0, transport);
		}
		else {
			pack(((Number) obj).shortValue(), transport);
		}
	}

	public void pack(short val, ITransport transport) throws IOException
	{
		buffer[0] = (byte) ((val >> 8) & 0xff);
		buffer[1] = (byte) (val & 0xff);
		_write(transport, buffer);
	}

	@Override
	public Object unpack(ITransport transport) throws IOException
	{
		_read(transport, buffer);
		return new Short(
				(short) (((buffer[0] & 0xff) << 8) | (buffer[1] & 0xff)));
	}
}
