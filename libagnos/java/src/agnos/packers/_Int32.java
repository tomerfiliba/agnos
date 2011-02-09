package agnos.packers;

import java.io.IOException;
import agnos.transports.ITransport;

public final class _Int32 extends AbstractPacker
{
	private byte[] buffer = new byte[4];

	protected _Int32()
	{
	}

	@Override
	public int getId()
	{
		return 4;
	}

	@Override
	public void pack(Object obj, ITransport transport) throws IOException
	{
		if (obj == null) {
			pack(0, transport);
		}
		else {
			pack(((Number) obj).intValue(), transport);
		}
	}

	public void pack(int val, ITransport transport) throws IOException
	{
		buffer[0] = (byte) ((val >> 24) & 0xff);
		buffer[1] = (byte) ((val >> 16) & 0xff);
		buffer[2] = (byte) ((val >> 8) & 0xff);
		buffer[3] = (byte) (val & 0xff);
		_write(transport, buffer);
	}

	@Override
	public Object unpack(ITransport transport) throws IOException
	{
		_read(transport, buffer);
		return new Integer(((int) (buffer[0] & 0xff) << 24)
				| ((int) (buffer[1] & 0xff) << 16)
				| ((int) (buffer[2] & 0xff) << 8)
				| (int) (buffer[3] & 0xff));
	}
}
