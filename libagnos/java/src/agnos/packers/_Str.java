package agnos.packers;

import java.io.IOException;
import agnos.transports.ITransport;

public final class _Str extends AbstractPacker
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
	public void pack(Object obj, ITransport transport) throws IOException
	{
		if (obj == null) {
			Builtin.Buffer.pack(null, transport);
		}
		else {
			Builtin.Buffer.pack(((String) obj).getBytes(encoding), transport);
		}
	}

	@Override
	public Object unpack(ITransport transport) throws IOException
	{
		byte[] buf = (byte[]) Builtin.Buffer.unpack(transport);
		return new String(buf, encoding);
	}
}
