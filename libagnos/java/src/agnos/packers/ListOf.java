package agnos.packers;

import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.util.ArrayList;
import java.util.List;

public class ListOf<T> extends AbstractPacker
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
	public void pack(Object obj, OutputStream stream) throws IOException
	{
		if (obj == null) {
			Builtin.Int32.pack(0, stream);
		}
		else if (obj.getClass().isArray()) {
			T[] arr = (T[])obj;
			Builtin.Int32.pack(arr.length, stream);

			for (T item : arr) {
				type.pack(item, stream);
			}
		}
		else {
			List<T> lst = (List<T>)obj;
			Builtin.Int32.pack(lst.size(), stream);

			for (T item : lst) {
				type.pack(item, stream);
			}
		}
	}

	@Override
	public Object unpack(InputStream stream) throws IOException
	{
		int length = (Integer) Builtin.Int32.unpack(stream);
		List<T> lst = new ArrayList<T>(length);
		for (int i = 0; i < length; i++) {
			lst.add((T)(type.unpack(stream)));
		}
		return lst;
	}
}