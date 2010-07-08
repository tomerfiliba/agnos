package agnos;

import java.io.*;
import java.util.*;


public class Packers
{
	public static final int CUSTOM_PACKER_ID_BASE = 2000;

	public static class UnknownPackerId extends IOException
	{
		public UnknownPackerId(String message)
		{
			super(message);
		}
	}

	// ////////////////////////////////////////////////////////////////////////

	public static abstract class AbstractPacker
	{
		abstract public void pack(Object obj, OutputStream stream)
				throws IOException;

		abstract public Object unpack(InputStream stream) throws IOException;

		abstract protected int getId();

		public void pack(Object obj, Transports.ITransport transport)
				throws IOException
		{
			pack(obj, transport.getOutputStream());
		}

		public Object unpack(Transports.ITransport transport)
				throws IOException
		{
			return unpack(transport.getInputStream());
		}

		// private static String repr(byte[] buffer) {
		// StringBuilder sb = new StringBuilder(buffer.length);
		// int b;
		// String s;
		//
		// for (int i = 0; i < buffer.length; i++) {
		// b = buffer[i] & 0xff;
		// if (b >= 32 && b <= 127) {
		// sb.append((char) b);
		// } else {
		// s = Integer.toString(b, 16);
		// if (s.length() == 1) {
		// s = "0" + s;
		// }
		// sb.append("\\x" + s);
		// }
		// }
		// return sb.toString();
		// }

		protected static void _write(OutputStream stream, byte[] buffer)
				throws IOException
		{
			// System.err.println("W: " + repr(buffer));
			stream.write(buffer, 0, buffer.length);
		}

		protected static void _read(InputStream stream, byte[] buffer)
				throws IOException
		{
			int total_got = 0;
			int got;

			while (total_got < buffer.length) {
				got = stream.read(buffer, total_got, buffer.length - total_got);
				total_got += got;
				if (got <= 0 && total_got < buffer.length) {
					throw new EOFException("premature end of stream detected");
				}
			}

			// System.err.println("R: " + repr(buffer));
		}

	}

	// ////////////////////////////////////////////////////////////////////////

	public static class _MockupPacker extends AbstractPacker
	{
		protected _MockupPacker()
		{
		}

		protected int getId()
		{
			throw new AssertionError("cannot use MockupPacker");
		}

		public void pack(Object obj, OutputStream stream) throws IOException
		{
		}

		public Object unpack(InputStream stream) throws IOException
		{
			return null;
		}
	}

	public static _MockupPacker MockupPacker = new _MockupPacker();

	// ////////////////////////////////////////////////////////////////////////

	public static class _Int8 extends AbstractPacker
	{
		private byte[] buffer = new byte[1];

		protected _Int8()
		{
		}

		protected int getId()
		{
			return 1;
		}

		public void pack(Object obj, OutputStream stream) throws IOException
		{
			if (obj == null) {
				pack((byte) 0, stream);
			}
			else {
				pack(((Number) obj).byteValue(), stream);
			}
		}

		public void pack(byte val, OutputStream stream) throws IOException
		{
			buffer[0] = val;
			_write(stream, buffer);
		}

		public Object unpack(InputStream stream) throws IOException
		{
			_read(stream, buffer);
			return new Byte(buffer[0]);
		}
	}

	public static final _Int8 Int8 = new _Int8();

	// ////////////////////////////////////////////////////////////////////////

	public static class _Bool extends AbstractPacker
	{
		protected _Bool()
		{
		}

		protected int getId()
		{
			return 2;
		}

		public void pack(Object obj, OutputStream stream) throws IOException
		{
			if (obj == null) {
				pack(false, stream);
			}
			else {
				pack(((Boolean) obj).booleanValue(), stream);
			}
		}

		public void pack(boolean val, OutputStream stream) throws IOException
		{
			if (val) {
				Int8.pack((byte) 1, stream);
			}
			else {
				Int8.pack((byte) 0, stream);
			}
		}

		public Object unpack(InputStream stream) throws IOException
		{
			return new Boolean((((Byte) Int8.unpack(stream))).byteValue() != 0);
		}
	}

	public static final _Bool Bool = new _Bool();

	// ////////////////////////////////////////////////////////////////////////

	public static class _Int16 extends AbstractPacker
	{
		private byte[] buffer = new byte[2];

		protected _Int16()
		{
		}

		protected int getId()
		{
			return 3;
		}

		public void pack(Object obj, OutputStream stream) throws IOException
		{
			if (obj == null) {
				pack((short) 0, stream);
			}
			else {
				pack(((Number) obj).shortValue(), stream);
			}
		}

		public void pack(short val, OutputStream stream) throws IOException
		{
			buffer[0] = (byte) ((val >> 8) & 0xff);
			buffer[1] = (byte) (val & 0xff);
			_write(stream, buffer);
		}

		public Object unpack(InputStream stream) throws IOException
		{
			_read(stream, buffer);
			return new Short(
					(short) (((buffer[0] & 0xff) << 8) | (buffer[1] & 0xff)));
		}
	}

	public static final _Int16 Int16 = new _Int16();

	// ////////////////////////////////////////////////////////////////////////

	public static class _Int32 extends AbstractPacker
	{
		private byte[] buffer = new byte[4];

		protected _Int32()
		{
		}

		protected int getId()
		{
			return 4;
		}

		public void pack(Object obj, OutputStream stream) throws IOException
		{
			if (obj == null) {
				pack(0, stream);
			}
			else {
				pack(((Number) obj).intValue(), stream);
			}
		}

		public void pack(int val, OutputStream stream) throws IOException
		{
			buffer[0] = (byte) ((val >> 24) & 0xff);
			buffer[1] = (byte) ((val >> 16) & 0xff);
			buffer[2] = (byte) ((val >> 8) & 0xff);
			buffer[3] = (byte) (val & 0xff);
			_write(stream, buffer);
		}

		public Object unpack(InputStream stream) throws IOException
		{
			_read(stream, buffer);
			return new Integer(((int) (buffer[0] & 0xff) << 24)
					| ((int) (buffer[1] & 0xff) << 16)
					| ((int) (buffer[2] & 0xff) << 8)
					| (int) (buffer[3] & 0xff));
		}
	}

	public static final _Int32 Int32 = new _Int32();

	// ////////////////////////////////////////////////////////////////////////

	public static class _Int64 extends AbstractPacker
	{
		private byte[] buffer = new byte[8];

		protected _Int64()
		{
		}

		protected int getId()
		{
			return 5;
		}

		public void pack(Object obj, OutputStream stream) throws IOException
		{
			if (obj == null) {
				pack((long) 0, stream);
			}
			else {
				pack(((Number) obj).longValue(), stream);
			}
		}

		public void pack(long val, OutputStream stream) throws IOException
		{
			buffer[0] = (byte) ((val >> 56) & 0xff);
			buffer[1] = (byte) ((val >> 48) & 0xff);
			buffer[2] = (byte) ((val >> 40) & 0xff);
			buffer[3] = (byte) ((val >> 32) & 0xff);
			buffer[4] = (byte) ((val >> 24) & 0xff);
			buffer[5] = (byte) ((val >> 16) & 0xff);
			buffer[6] = (byte) ((val >> 8) & 0xff);
			buffer[7] = (byte) (val & 0xff);
			_write(stream, buffer);
		}

		public Object unpack(InputStream stream) throws IOException
		{
			_read(stream, buffer);

			return new Long(((long) (buffer[0] & 0xff) << 56)
					| ((long) (buffer[1] & 0xff) << 48)
					| ((long) (buffer[2] & 0xff) << 40)
					| ((long) (buffer[3] & 0xff) << 32)
					| ((long) (buffer[4] & 0xff) << 24)
					| ((long) (buffer[5] & 0xff) << 16)
					| ((long) (buffer[6] & 0xff) << 8)
					| (long) (buffer[7] & 0xff));
		}
	}

	public static final _Int64 Int64 = new _Int64();

	// ////////////////////////////////////////////////////////////////////////
	public interface ISerializer
	{
		Long store(Object obj);

		Object load(Long id);
	}

	public static class ObjRef extends AbstractPacker
	{
		protected ISerializer serializer;
		private int id;

		public ObjRef(int id, ISerializer serializer)
		{
			this.id = id;
			this.serializer = serializer;
		}

		protected int getId()
		{
			return id;
		}

		public void pack(Object obj, OutputStream stream) throws IOException
		{
			Long obj2 = serializer.store(obj);
			Int64.pack(obj2, stream);
		}

		public Object unpack(InputStream stream) throws IOException
		{
			Long obj = (Long) Int64.unpack(stream);
			return serializer.load(obj);
		}
	}

	// ////////////////////////////////////////////////////////////////////////

	public static class _Float extends AbstractPacker
	{
		protected _Float()
		{
		}

		protected int getId()
		{
			return 6;
		}

		public void pack(Object obj, OutputStream stream) throws IOException
		{
			if (obj == null) {
				pack(0.0, stream);
			}
			else {
				pack(((Number) obj).doubleValue(), stream);
			}
		}

		public void pack(double val, OutputStream stream) throws IOException
		{
			Int64.pack(Double.doubleToLongBits(val), stream);
		}

		public Object unpack(InputStream stream) throws IOException
		{
			return new Double(Double.longBitsToDouble(((Long) (Int64
					.unpack(stream))).longValue()));
		}
	}

	public static final _Float Float = new _Float();

	// ////////////////////////////////////////////////////////////////////////

	public static class _Buffer extends AbstractPacker
	{
		protected _Buffer()
		{
		}

		protected int getId()
		{
			return 7;
		}

		public void pack(Object obj, OutputStream stream) throws IOException
		{
			if (obj == null) {
				Int32.pack(0, stream);
			}
			else {
				byte[] val = (byte[]) obj;
				Int32.pack(val.length, stream);
				_write(stream, val);
			}
		}

		public Object unpack(InputStream stream) throws IOException
		{
			int length = (Integer) Int32.unpack(stream);
			byte[] buf = new byte[length];
			_read(stream, buf);
			return buf;
		}
	}

	public static final _Buffer Buffer = new _Buffer();

	// ////////////////////////////////////////////////////////////////////////

	public static class _Date extends AbstractPacker
	{
		protected _Date()
		{
		}

		protected int getId()
		{
			return 8;
		}

		public void pack(Object obj, OutputStream stream) throws IOException
		{
			Int64.pack(new Long(((Date) obj).getTime()), stream);
		}

		public Object unpack(InputStream stream) throws IOException
		{
			return new Date((Long) Int64.unpack(stream));
		}
	}

	public static final _Date Date = new _Date();

	// ////////////////////////////////////////////////////////////////////////

	public static class _Str extends AbstractPacker
	{
		private static final String encoding = "UTF-8";

		protected _Str()
		{
		}

		protected int getId()
		{
			return 9;
		}

		public void pack(Object obj, OutputStream stream) throws IOException
		{
			if (obj == null) {
				Buffer.pack(null, stream);
			}
			else {
				Buffer.pack(((String) obj).getBytes(encoding), stream);
			}
		}

		public Object unpack(InputStream stream) throws IOException
		{
			byte[] buf = (byte[]) Buffer.unpack(stream);
			return new String(buf, encoding);
		}
	}

	public static final _Str Str = new _Str();

	// ////////////////////////////////////////////////////////////////////////

	public static class ListOf extends AbstractPacker
	{
		private AbstractPacker type;
		private int id;

		public ListOf(int id, AbstractPacker type)
		{
			this.id = id;
			this.type = type;
		}

		protected int getId()
		{
			return id;
		}

		public void pack(Object obj, OutputStream stream) throws IOException
		{
			if (obj == null) {
				Int32.pack(0, stream);
			}
			else {
				List val = (List) obj;
				Int32.pack(val.size(), stream);

				for (Object obj2 : val) {
					type.pack(obj2, stream);
				}
			}
		}

		public Object unpack(InputStream stream) throws IOException
		{
			int length = (Integer) Int32.unpack(stream);
			ArrayList<Object> arr = new ArrayList<Object>(length);
			for (int i = 0; i < length; i++) {
				arr.add(type.unpack(stream));
			}
			return arr;
		}
	}

	public static final ListOf listOfInt8 = new ListOf(800, Int8);
	public static final ListOf listOfBool = new ListOf(801, Bool);
	public static final ListOf listOfInt16 = new ListOf(802, Int16);
	public static final ListOf listOfInt32 = new ListOf(803, Int32);
	public static final ListOf listOfInt64 = new ListOf(804, Int64);
	public static final ListOf listOfFloat = new ListOf(805, Float);
	public static final ListOf listOfBuffer = new ListOf(806, Buffer);
	public static final ListOf listOfDate = new ListOf(807, Date);
	public static final ListOf listOfStr = new ListOf(808, Str);

	// ////////////////////////////////////////////////////////////////////////

	public static class MapOf extends AbstractPacker
	{
		private AbstractPacker keytype;
		private AbstractPacker valtype;
		private int id;

		public MapOf(int id, AbstractPacker keytype, AbstractPacker valtype)
		{
			this.id = id;
			this.keytype = keytype;
			this.valtype = valtype;
		}

		protected int getId()
		{
			return id;
		}

		public void pack(Object obj, OutputStream stream) throws IOException
		{
			if (obj == null) {
				Int32.pack(0, stream);
			}
			else {
				Map val = (Map) obj;
				Int32.pack(val.size(), stream);

				for (Map.Entry e : (Set<Map.Entry>) val.entrySet()) {
					keytype.pack(e.getKey(), stream);
					valtype.pack(e.getValue(), stream);
				}
			}
		}

		public Object unpack(InputStream stream) throws IOException
		{
			int length = (Integer) Int32.unpack(stream);
			Map<Object, Object> map = new HashMap<Object, Object>(length);
			for (int i = 0; i < length; i++) {
				Object k = keytype.unpack(stream);
				Object v = valtype.unpack(stream);
				map.put(k, v);
			}
			return map;
		}
	}

	public static final MapOf mapOfInt32Int32 = new MapOf(850, Int32, Int32);
	public static final MapOf mapOfInt32Str = new MapOf(851, Int32, Str);
	public static final MapOf mapOfStrInt32 = new MapOf(852, Str, Int32);
	public static final MapOf mapOfStrStr = new MapOf(853, Str, Str);

	// ////////////////////////////////////////////////////////////////////////

	public static class HeteroMapPacker extends AbstractPacker
	{
		protected Map<Integer, AbstractPacker> packersMap;
		private int id;

		public HeteroMapPacker(int id, Map<Integer, AbstractPacker> packersMap)
		{
			this.id = id;
			this.packersMap = packersMap;
		}

		protected int getId()
		{
			return id;
		}

		public void pack(Object obj, OutputStream stream) throws IOException
		{
			HeteroMap map = (HeteroMap) obj;
			if (map == null) {
				Int32.pack(0, stream);
			}
			else {
				Int32.pack(map.size(), stream);
				for (Map.Entry e : map.entrySet()) {
					Object key = e.getKey();
					Object val = e.getValue();
					AbstractPacker keypacker = map.getKeyPacker(key);
					AbstractPacker valpacker = map.getValuePacker(key);

					Int32.pack(keypacker.getId(), stream);
					keypacker.pack(key, stream);

					Int32.pack(valpacker.getId(), stream);
					valpacker.pack(val, stream);
				}
			}
		}

		public Object unpack(InputStream stream) throws IOException
		{
			int length = (Integer) Int32.unpack(stream);
			HeteroMap map = new HeteroMap(length);

			for (int i = 0; i < length; i++) {
				Integer keypid = (Integer) Int32.unpack(stream);
				AbstractPacker keypacker = getPacker(keypid);
				Object key = keypacker.unpack(stream);

				Integer valpid = (Integer) Int32.unpack(stream);
				AbstractPacker valpacker = getPacker(valpid);
				Object val = valpacker.unpack(stream);

				map.put(key, keypacker, val, valpacker);
			}
			return map;
		}

		protected AbstractPacker getPacker(Integer id) throws UnknownPackerId
		{
			switch (id) {
			case 1:
				return Int8;
			case 2:
				return Bool;
			case 3:
				return Int16;
			case 4:
				return Int32;
			case 5:
				return Int64;
			case 6:
				return Float;
			case 7:
				return Buffer;
			case 8:
				return Date;
			case 9:
				return Str;
			case 800:
				return listOfInt8;
			case 801:
				return listOfBool;
			case 802:
				return listOfInt16;
			case 803:
				return listOfInt32;
			case 804:
				return listOfInt64;
			case 805:
				return listOfFloat;
			case 806:
				return listOfBuffer;
			case 807:
				return listOfDate;
			case 808:
				return listOfStr;
			case 850:
				return mapOfInt32Int32;
			case 851:
				return mapOfInt32Str;
			case 852:
				return mapOfStrInt32;
			case 853:
				return mapOfStrStr;
			case 998:
				return builtinHeteroMapPacker;
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

	public static final HeteroMapPacker builtinHeteroMapPacker = new HeteroMapPacker(
			998, null);
}
