package agnos.packers;

import java.io.IOException;
import agnos.transports.ITransport;

public final class ObjRef extends AbstractPacker
{
	protected ISerializer serializer;
	protected int id;

	public ObjRef(int id, ISerializer serializer)
	{
		this.id = id;
		this.serializer = serializer;
	}

	@Override
	public int getId()
	{
		return id;
	}

	@Override
	public void pack(Object obj, ITransport transport) throws IOException
	{
		Long obj2 = serializer.store(obj);
		Builtin.Int64.pack(obj2, transport);
	}

	@Override
	public Object unpack(ITransport transport) throws IOException
	{
		Long obj = (Long) Builtin.Int64.unpack(transport);
		return serializer.load(obj);
	}
}
