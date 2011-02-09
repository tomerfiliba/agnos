package agnos.packers;

import java.io.IOException;
import agnos.transports.ITransport;


public final class _Int8 extends AbstractPacker
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
	public void pack(Object obj, ITransport transport) throws IOException
	{
		if (obj == null) {
			pack((byte) 0, transport);
		}
		else {
			pack(((Number) obj).byteValue(), transport);
		}
	}

	public void pack(byte val, ITransport transport) throws IOException
	{
		buffer[0] = val;
		_write(transport, buffer);
	}

	@Override
	public Object unpack(ITransport transport) throws IOException
	{
		_read(transport, buffer);
		return new Byte(buffer[0]);
	}
}