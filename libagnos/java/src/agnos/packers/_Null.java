package agnos.packers;

import java.io.IOException;
import agnos.transports.ITransport;


public final class _Null extends AbstractPacker
{
	protected _Null()
	{
	}

	@Override
	public int getId()
	{
		return 10;
	}
	
	@Override
	public void pack(Object obj, ITransport transport) throws IOException
	{
	}

	@Override
	public Object unpack(ITransport transport) throws IOException
	{
		return null;
	}
}