package agnos.packers;

import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;

public class ObjRef extends AbstractPacker
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
	public void pack(Object obj, OutputStream stream) throws IOException
	{
		Long obj2 = serializer.store(obj);
		Builtin.Int64.pack(obj2, stream);
	}

	@Override
	public Object unpack(InputStream stream) throws IOException
	{
		Long obj = (Long) Builtin.Int64.unpack(stream);
		return serializer.load(obj);
	}
}
