package agnos.packers;

import java.io.IOException;
import agnos.transports.ITransport;

public final class _Buffer extends AbstractPacker
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
	public void pack(Object obj, ITransport transport) throws IOException
	{
		if (obj == null) {
			Builtin.Int32.pack(0, transport);
		}
		else {
			byte[] val = (byte[]) obj;
			Builtin.Int32.pack(val.length, transport);
			_write(transport, val);
		}
	}

	@Override
	public Object unpack(ITransport transport) throws IOException
	{
		int length = (Integer) Builtin.Int32.unpack(transport);
		byte[] buf = new byte[length];
		_read(transport, buf);
		return buf;
	}
}
