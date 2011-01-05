package agnos.packers;

import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;


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
	public void pack(Object obj, OutputStream stream) throws IOException
	{
	}

	@Override
	public Object unpack(InputStream stream) throws IOException
	{
		return null;
	}
}