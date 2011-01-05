package agnos.packers;

import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.util.HashMap;
import java.util.Map;
import java.util.Set;

public class MapOf<K, V> extends AbstractPacker
{
	protected AbstractPacker keytype;
	protected AbstractPacker valtype;
	protected int id;

	public MapOf(int id, AbstractPacker keytype, AbstractPacker valtype)
	{
		this.id = id;
		this.keytype = keytype;
		this.valtype = valtype;
		if (keytype == null || valtype == null) {
			throw new AssertionError("type is null!");
		}
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
			Map<K, V> val = (Map<K, V>) obj;
			Builtin.Int32.pack(val.size(), stream);

			for (Map.Entry<K, V> e : (Set<Map.Entry<K, V>>) val.entrySet()) {
				keytype.pack(e.getKey(), stream);
				valtype.pack(e.getValue(), stream);
			}
		}
	}

	@Override
	public Object unpack(InputStream stream) throws IOException
	{
		int length = (Integer) Builtin.Int32.unpack(stream);
		Map<K, V> map = new HashMap<K, V>(length);
		for (int i = 0; i < length; i++) {
			K k = (K)(keytype.unpack(stream));
			V v = (V)(valtype.unpack(stream));
			map.put(k, v);
		}
		return map;
	}
}
