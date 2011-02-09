package agnos.packers;

import java.io.IOException;
import java.util.Date;
import agnos.transports.ITransport;

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
	public void pack(Object obj, ITransport transport) throws IOException
	{
		long microsecs = ((Date) obj).getTime() * 1000;
		Builtin.Int64.pack(new Long(UNIX_EPOCH_UTC_MICROSECS + microsecs), transport);
	}

	@Override
	public Object unpack(ITransport transport) throws IOException
	{
		long microsecs = (Long)Builtin.Int64.unpack(transport);
		return new Date((microsecs - UNIX_EPOCH_UTC_MICROSECS) / 1000);
	}
}
