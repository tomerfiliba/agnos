package agnos.util;

import java.io.IOException;
import java.util.Map;

import agnos.transports.ITransport;
import agnos.packers.AbstractPacker;
import agnos.packers.Builtin;

public class _HeteroMapPacker extends AbstractPacker
{
	protected Map<Integer, AbstractPacker> packersMap;
	protected int id;

	public _HeteroMapPacker(int id, Map<Integer, AbstractPacker> packersMap)
	{
		this.id = id;
		this.packersMap = packersMap;
	}

	@Override
	public int getId()
	{
		return id;
	}

	@Override
	public void pack(Object obj, ITransport transport) throws IOException
	{
		HeteroMap map = (HeteroMap) obj;
		if (map == null) {
			Builtin.Int32.pack(0, transport);
		}
		else {
			Builtin.Int32.pack(map.size(), transport);
			for (Map.Entry<Object, Object> e : map.entrySet()) {
				Object key = e.getKey();
				Object val = e.getValue();
				AbstractPacker keypacker = map.getKeyPacker(key);
				AbstractPacker valpacker = map.getValuePacker(key);

				Builtin.Int32.pack(keypacker.getId(), transport);
				keypacker.pack(key, transport);

				Builtin.Int32.pack(valpacker.getId(), transport);
				valpacker.pack(val, transport);
			}
		}
	}

	@Override
	public Object unpack(ITransport transport) throws IOException
	{
		int length = (Integer) Builtin.Int32.unpack(transport);
		HeteroMap hmap = new HeteroMap(length);

		for (int i = 0; i < length; i++) {
			Integer keypid = (Integer) Builtin.Int32.unpack(transport);
			AbstractPacker keypacker = getPacker(keypid);
			Object key = keypacker.unpack(transport);

			Integer valpid = (Integer) Builtin.Int32.unpack(transport);
			AbstractPacker valpacker = getPacker(valpid);
			Object val = valpacker.unpack(transport);

			hmap.put(key, keypacker, val, valpacker);
		}
		return hmap;
	}

	protected AbstractPacker getPacker(Integer id) throws UnknownPackerId
	{
		switch (id) {
		case 1:
			return Builtin.Int8;
		case 2:
			return Builtin.Bool;
		case 3:
			return Builtin.Int16;
		case 4:
			return Builtin.Int32;
		case 5:
			return Builtin.Int64;
		case 6:
			return Builtin.Float;
		case 7:
			return Builtin.Buffer;
		case 8:
			return Builtin.Date;
		case 9:
			return Builtin.Str;
		case 10:
			return Builtin.Null;
		case 800:
			return Builtin.listOfInt8;
		case 801:
			return Builtin.listOfBool;
		case 802:
			return Builtin.listOfInt16;
		case 803:
			return Builtin.listOfInt32;
		case 804:
			return Builtin.listOfInt64;
		case 805:
			return Builtin.listOfFloat;
		case 806:
			return Builtin.listOfBuffer;
		case 807:
			return Builtin.listOfDate;
		case 808:
			return Builtin.listOfStr;
		case 820:
			return Builtin.setOfInt8;
		case 821:
			return Builtin.setOfBool;
		case 822:
			return Builtin.setOfInt16;
		case 823:
			return Builtin.setOfInt32;
		case 824:
			return Builtin.setOfInt64;
		case 825:
			return Builtin.setOfFloat;
		case 826:
			return Builtin.setOfBuffer;
		case 827:
			return Builtin.setOfDate;
		case 828:
			return Builtin.setOfStr;
		case 850:
			return Builtin.mapOfInt32Int32;
		case 851:
			return Builtin.mapOfInt32Str;
		case 852:
			return Builtin.mapOfStrInt32;
		case 853:
			return Builtin.mapOfStrStr;
		case 998:
			return Builtin.heteroMapPacker;
		default:
			//if (id < CUSTOM_PACKER_ID_BASE) {
			//	throw new UnknownPackerId("packer id too low" + id);
			//}
			if (packersMap == null) {
				throw new UnknownPackerId("unknown packer id " + id);
			}
			AbstractPacker packer = (AbstractPacker) packersMap.get(id);
			if (packer == null) {
				throw new UnknownPackerId("unknown packer id " + id);
			}
			return packer;
		}
	}
}
