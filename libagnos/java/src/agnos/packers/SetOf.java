package agnos.packers;

import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.util.HashSet;
import java.util.Set;

public class SetOf<T> extends AbstractPacker
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
	public void pack(Object obj, OutputStream stream) throws IOException
	{
		if (obj == null) {
			Builtin.Int32.pack(0, stream);
		}
		else {
			Set<T> set = (Set<T>)obj;
			Builtin.Int32.pack(set.size(), stream);

			for (Object item : set) {
				type.pack(item, stream);
			}
		}
	}

	@Override
	public Object unpack(InputStream stream) throws IOException
	{
		int length = (Integer) Builtin.Int32.unpack(stream);
		Set<T> set = new HashSet<T>(length);
		for (int i = 0; i < length; i++) {
			set.add((T)(type.unpack(stream)));
		}
		return set;
	}
}
