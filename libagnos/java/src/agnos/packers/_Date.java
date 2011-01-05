package agnos.packers;

import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.util.Date;

public final class _Date extends AbstractPacker
{
	private static final long UNIX_EPOCH_UTC_MICROSECS = 62135596800000000L;
	
	protected _Date()
	{
	}

	@Override
	public int getId()
	{
		return 8;
	}
	
	@Override
	public void pack(Object obj, OutputStream stream) throws IOException
	{
		long microsecs = ((Date) obj).getTime() * 1000;
		Builtin.Int64.pack(new Long(UNIX_EPOCH_UTC_MICROSECS + microsecs), stream);
	}

	@Override
	public Object unpack(InputStream stream) throws IOException
	{
		long microsecs = (Long)Builtin.Int64.unpack(stream);
		return new Date((microsecs - UNIX_EPOCH_UTC_MICROSECS) / 1000);
	}
}
