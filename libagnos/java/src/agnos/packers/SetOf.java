package agnos.packers;

import java.io.IOException;
import java.util.HashSet;
import java.util.Set;
import agnos.transports.ITransport;

public final class SetOf<T> extends AbstractPacker
{
	protected AbstractPacker type;
	protected int id;

	public SetOf(int id, AbstractPacker type)
	{
		if (type == null) {
			throw new AssertionError("type is null!");
		}
		this.id = id;
		this.type = type;
	}

	@Override
	public int getId()
	{
		return id;
	}

	@Override
	public void pack(Object obj, ITransport transport) throws IOException
	{
		if (obj == null) {
			Builtin.Int32.pack(0, transport);
		}
		else {
			Set<? extends T> set = (Set<? extends T>)obj;
			Builtin.Int32.pack(set.size(), transport);

			for (Object item : set) {
				type.pack(item, transport);
			}
		}
	}

	@Override
	public Object unpack(ITransport transport) throws IOException
	{
		int length = (Integer) Builtin.Int32.unpack(transport);
		Set<T> set = new HashSet<T>(length);
		for (int i = 0; i < length; i++) {
			set.add((T)(type.unpack(transport)));
		}
		return set;
	}
}
