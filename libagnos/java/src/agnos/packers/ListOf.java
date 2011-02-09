package agnos.packers;

import java.io.IOException;
import java.util.ArrayList;
import java.util.List;
import agnos.transports.ITransport;


public final class ListOf<T> extends AbstractPacker
{
	protected AbstractPacker type;
	protected int id;

	public ListOf(int id, AbstractPacker type)
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
		else if (obj.getClass().isArray()) {
			T[] arr = (T[])obj;
			Builtin.Int32.pack(arr.length, transport);

			for (T item : arr) {
				type.pack(item, transport);
			}
		}
		else {
			List<? extends T> lst = (List<? extends T>)obj;
			Builtin.Int32.pack(lst.size(), transport);

			for (T item : lst) {
				type.pack(item, transport);
			}
		}
	}

	@Override
	public Object unpack(ITransport transport) throws IOException
	{
		int length = (Integer) Builtin.Int32.unpack(transport);
		List<T> lst = new ArrayList<T>(length);
		for (int i = 0; i < length; i++) {
			lst.add((T)(type.unpack(transport)));
		}
		return lst;
	}
}