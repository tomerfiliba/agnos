package agnos.packers;

import java.io.IOException;
import java.util.HashMap;
import java.util.Map;
import java.util.Set;
import agnos.transports.ITransport;

public final class MapOf<K, V> extends AbstractPacker
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
	public void pack(Object obj, ITransport transport) throws IOException
	{
		if (obj == null) {
			Builtin.Int32.pack(0, transport);
		}
		else {
			Map<K, V> val = (Map<K, V>) obj;
			Builtin.Int32.pack(val.size(), transport);

			for (Map.Entry<K, V> e : (Set<Map.Entry<K, V>>) val.entrySet()) {
				keytype.pack(e.getKey(), transport);
				valtype.pack(e.getValue(), transport);
			}
		}
	}

	@Override
	public Object unpack(ITransport transport) throws IOException
	{
		int length = (Integer) Builtin.Int32.unpack(transport);
		Map<K, V> map = new HashMap<K, V>(length);
		for (int i = 0; i < length; i++) {
			K k = (K)(keytype.unpack(transport));
			V v = (V)(valtype.unpack(transport));
			map.put(k, v);
		}
		return map;
	}
}
