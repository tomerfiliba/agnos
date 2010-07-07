package agnos;

import java.io.*;
import java.util.*;

public class Packers {
	public static final int BUILTIN_PACKER_ID_BASE = 1000;
	public static final int CUSTOM_PACKER_ID_BASE = 2000;
	
	public static class UnknownPackerId extends IOException
	{
		public UnknownPackerId(String message) {
			super(message);
		}
	}
	
	public static abstract class BasePacker {
		abstract public void pack(Object obj, OutputStream stream)
				throws IOException;

		abstract public Object unpack(InputStream stream) throws IOException;

		abstract protected int getId();
		
		public void pack(Object obj, Transports.ITransport transport)
				throws IOException {
			pack(obj, transport.getOutputStream());
		}

		public Object unpack(Transports.ITransport transport)
				throws IOException {
			return unpack(transport.getInputStream());
		}

//		private static String repr(byte[] buffer) {
//			StringBuilder sb = new StringBuilder(buffer.length);
//			int b;
//			String s;
//
//			for (int i = 0; i < buffer.length; i++) {
//				b = buffer[i] & 0xff;
//				if (b >= 32 && b <= 127) {
//					sb.append((char) b);
//				} else {
//					s = Integer.toString(b, 16);
//					if (s.length() == 1) {
//						s = "0" + s;
//					}
//					sb.append("\\x" + s);
//				}
//			}
//			return sb.toString();
//		}
		
		protected static void _write(OutputStream stream, byte[] buffer)
				throws IOException {
			// System.err.println("W: " + repr(buffer));
			stream.write(buffer, 0, buffer.length);
		}

		protected static void _read(InputStream stream, byte[] buffer)
				throws IOException {
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

	public static class _MockupPacker extends BasePacker {
		protected _MockupPacker() {
		}

		protected int getId() {
			throw new AssertionError("cannot use MockupPacker");
		}

		public void pack(Object obj, OutputStream stream) throws IOException {
		}

		public Object unpack(InputStream stream) throws IOException {
			return null;
		}
	}

	public static _MockupPacker MockupPacker = new _MockupPacker();

	// ////////////////////////////////////////////////////////////////////////

	public static class _Int8 extends BasePacker {
		private byte[] buffer = new byte[1];

		protected _Int8() {
		}

		protected int getId() {
			return 1;
		}

		public void pack(Object obj, OutputStream stream) throws IOException {
			if (obj == null) {
				pack((byte) 0, stream);
			} else {
				pack(((Number) obj).byteValue(), stream);
			}
		}

		public void pack(byte val, OutputStream stream) throws IOException {
			buffer[0] = val;
			_write(stream, buffer);
		}

		public Object unpack(InputStream stream) throws IOException {
			_read(stream, buffer);
			return new Byte(buffer[0]);
		}
	}

	public static _Int8 Int8 = new _Int8();

	// ////////////////////////////////////////////////////////////////////////

	public static class _Bool extends BasePacker {
		protected _Bool() {
		}

		protected int getId() {
			return 2;
		}

		public void pack(Object obj, OutputStream stream) throws IOException {
			if (obj == null) {
				pack(false, stream);
			} else {
				pack(((Boolean) obj).booleanValue(), stream);
			}
		}

		public void pack(boolean val, OutputStream stream) throws IOException {
			if (val) {
				Int8.pack((byte) 1, stream);
			} else {
				Int8.pack((byte) 0, stream);
			}
		}

		public Object unpack(InputStream stream) throws IOException {
			return new Boolean((((Byte) Int8.unpack(stream))).byteValue() != 0);
		}
	}

	public static _Bool Bool = new _Bool();

	// ////////////////////////////////////////////////////////////////////////

	public static class _Int16 extends BasePacker {
		private byte[] buffer = new byte[2];

		protected _Int16() {
		}
		
		protected int getId() {
			return 3;
		}

		public void pack(Object obj, OutputStream stream) throws IOException {
			if (obj == null) {
				pack((short) 0, stream);
			} else {
				pack(((Number) obj).shortValue(), stream);
			}
		}

		public void pack(short val, OutputStream stream) throws IOException {
			buffer[0] = (byte) ((val >> 8) & 0xff);
			buffer[1] = (byte) (val & 0xff);
			_write(stream, buffer);
		}

		public Object unpack(InputStream stream) throws IOException {
			_read(stream, buffer);
			return new Short(
					(short) (((buffer[0] & 0xff) << 8) | (buffer[1] & 0xff)));
		}
	}

	public static _Int16 Int16 = new _Int16();

	// ////////////////////////////////////////////////////////////////////////

	public static class _Int32 extends BasePacker {
		private byte[] buffer = new byte[4];

		protected _Int32() {
		}

		protected int getId() {
			return 4;
		}

		public void pack(Object obj, OutputStream stream) throws IOException {
			if (obj == null) {
				pack(0, stream);
			} else {
				pack(((Number) obj).intValue(), stream);
			}
		}

		public void pack(int val, OutputStream stream) throws IOException {
			buffer[0] = (byte) ((val >> 24) & 0xff);
			buffer[1] = (byte) ((val >> 16) & 0xff);
			buffer[2] = (byte) ((val >> 8) & 0xff);
			buffer[3] = (byte) (val & 0xff);
			_write(stream, buffer);
		}

		public Object unpack(InputStream stream) throws IOException {
			_read(stream, buffer);
			return new Integer(((int) (buffer[0] & 0xff) << 24)
					| ((int) (buffer[1] & 0xff) << 16)
					| ((int) (buffer[2] & 0xff) << 8)
					| (int) (buffer[3] & 0xff));
		}
	}

	public static _Int32 Int32 = new _Int32();

	// ////////////////////////////////////////////////////////////////////////

	public static class _Int64 extends BasePacker {
		private byte[] buffer = new byte[8];

		protected _Int64() {
		}

		protected int getId() {
			return 5;
		}

		public void pack(Object obj, OutputStream stream) throws IOException {
			if (obj == null) {
				pack((long) 0, stream);
			} else {
				pack(((Number) obj).longValue(), stream);
			}
		}

		public void pack(long val, OutputStream stream) throws IOException {
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

		public Object unpack(InputStream stream) throws IOException {
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

	public static _Int64 Int64 = new _Int64();

	// ////////////////////////////////////////////////////////////////////////
	public interface ISerializer {
		Long store(Object obj);

		Object load(Long id);
	}

	public static class ObjRef extends BasePacker {
		protected ISerializer serializer;
		private int id;

		public ObjRef(int id, ISerializer serializer) {
			this.id = id;
			this.serializer = serializer;
		}

		protected int getId() {
			return id;
		}

		public void pack(Object obj, OutputStream stream) throws IOException {
			Long obj2 = serializer.store(obj);
			Int64.pack(obj2, stream);
		}

		public Object unpack(InputStream stream) throws IOException {
			Long obj = (Long) Int64.unpack(stream);
			return serializer.load(obj);
		}
	}

	// ////////////////////////////////////////////////////////////////////////

	public static class _Float extends BasePacker {
		protected _Float() {
		}

		protected int getId() {
			return 6;
		}

		public void pack(Object obj, OutputStream stream) throws IOException {
			if (obj == null) {
				pack(0.0, stream);
			} else {
				pack(((Number) obj).doubleValue(), stream);
			}
		}

		public void pack(double val, OutputStream stream) throws IOException {
			Int64.pack(Double.doubleToLongBits(val), stream);
		}

		public Object unpack(InputStream stream) throws IOException {
			return new Double(Double.longBitsToDouble(((Long) (Int64
					.unpack(stream))).longValue()));
		}
	}

	public static _Float Float = new _Float();

	// ////////////////////////////////////////////////////////////////////////

	public static class _Buffer extends BasePacker {
		protected _Buffer() {
		}

		protected int getId() {
			return 7;
		}

		public void pack(Object obj, OutputStream stream) throws IOException {
			if (obj == null) {
				Int32.pack(0, stream);
			} else {
				byte[] val = (byte[]) obj;
				Int32.pack(val.length, stream);
				_write(stream, val);
			}
		}

		public Object unpack(InputStream stream) throws IOException {
			int length = (Integer) Int32.unpack(stream);
			byte[] buf = new byte[length];
			_read(stream, buf);
			return buf;
		}
	}

	public static _Buffer Buffer = new _Buffer();

	// ////////////////////////////////////////////////////////////////////////

	public static class _Date extends BasePacker {
		protected _Date() {
		}

		protected int getId() {
			return 8;
		}

		public void pack(Object obj, OutputStream stream) throws IOException {
			Int64.pack(new Long(((Date) obj).getTime()), stream);
		}

		public Object unpack(InputStream stream) throws IOException {
			return new Date((Long) Int64.unpack(stream));
		}
	}

	public static _Date Date = new _Date();

	// ////////////////////////////////////////////////////////////////////////

	public static class _Str extends BasePacker {
		private static final String encoding = "UTF-8";

		protected _Str() {
		}

		protected int getId() {
			return 9;
		}

		public void pack(Object obj, OutputStream stream) throws IOException {
			if (obj == null) {
				Buffer.pack(null, stream);
			} else {
				Buffer.pack(((String) obj).getBytes(encoding), stream);
			}
		}

		public Object unpack(InputStream stream) throws IOException {
			byte[] buf = (byte[]) Buffer.unpack(stream);
			return new String(buf, encoding);
		}
	}

	public static _Str Str = new _Str();

	// ////////////////////////////////////////////////////////////////////////

	public static class ListOf extends BasePacker {
		private BasePacker type;
		private int id;

		public ListOf(int id, BasePacker type) {
			this.id = id;
			this.type = type;
		}

		protected int getId() {
			return id;
		}

		public void pack(Object obj, OutputStream stream) throws IOException {
			if (obj == null) {
				Int32.pack(0, stream);
			} else {
				List val = (List) obj;
				Int32.pack(val.size(), stream);

				for (Object obj2 : val) {
					type.pack(obj2, stream);
				}
			}
		}

		public Object unpack(InputStream stream) throws IOException {
			int length = (Integer) Int32.unpack(stream);
			ArrayList<Object> arr = new ArrayList<Object>(length);
			for (int i = 0; i < length; i++) {
				arr.add(type.unpack(stream));
			}
			return arr;
		}
	}

	// ////////////////////////////////////////////////////////////////////////

	public static class MapOf extends BasePacker {
		private BasePacker keytype;
		private BasePacker valtype;
		private int id;

		public MapOf(int id, BasePacker keytype, BasePacker valtype) {
			this.id = id;
			this.keytype = keytype;
			this.valtype = valtype;
		}

		protected int getId() {
			return id;
		}

		public void pack(Object obj, OutputStream stream) throws IOException {
			if (obj == null) {
				Int32.pack(0, stream);
			} else {
				Map val = (Map) obj;
				Int32.pack(val.size(), stream);

				for (Map.Entry e : (Set<Map.Entry>) val.entrySet()) {
					keytype.pack(e.getKey(), stream);
					valtype.pack(e.getValue(), stream);
				}
			}
		}

		public Object unpack(InputStream stream) throws IOException {
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

	// ////////////////////////////////////////////////////////////////////////
	
	protected static class DynamicRecordField
	{
		public BasePacker packer;
		public Object value;
		public DynamicRecordField(BasePacker packer)
		{
			this(packer, null);
		}
		public DynamicRecordField(BasePacker packer, Object value)
		{
			this.packer = packer;
			this.value = value;
		}
	}
	
	public static class DynamicRecord
	{
		protected Map<String, DynamicRecordField> fields;
		
		public DynamicRecord()
		{
			this(32);
		}
		public DynamicRecord(int capacity)
		{
			fields = new HashMap<String, DynamicRecordField>(capacity);
		}
		public DynamicRecord(DynamicRecord other)
		{
			fields = new HashMap<String, DynamicRecordField>(other.fields);
		}
		
		public void addField(String name, BasePacker packer)
		{
			fields.put(name, new DynamicRecordField(packer));
		}
		public void addField(String name, BasePacker packer, Object value)
		{
			fields.put(name, new DynamicRecordField(packer, value));
		}
		public void addField(String name, Byte value)
		{
			addField(name, Int8, value);
		}
		public void addField(String name, byte value)
		{
			addField(name, Int8, new Byte(value));
		}
		public void addField(String name, Boolean value)
		{
			addField(name, Bool, value);
		}
		public void addField(String name, boolean value)
		{
			addField(name, Int8, new Boolean(value));
		}
		public void addField(String name, Short value)
		{
			addField(name, Int16, value);
		}
		public void addField(String name, short value)
		{
			addField(name, Int16, new Short(value));
		}
		public void addField(String name, Integer value)
		{
			addField(name, Int32, value);
		}
		public void addField(String name, int value)
		{
			addField(name, Int32, new Integer(value));
		}
		public void addField(String name, Long value)
		{
			addField(name, Int64, value);
		}
		public void addField(String name, long value)
		{
			addField(name, Int64, new Long(value));
		}
		public void addField(String name, Double value)
		{
			addField(name, Float, value);
		}
		public void addField(String name, double value)
		{
			addField(name, Float, new Double(value));
		}
		public void addField(String name, String value)
		{
			addField(name, Str, value);
		}
		public void addField(String name, byte[] value)
		{
			addField(name, Buffer, value);
		}
		public void addField(String name, Date value)
		{
			addField(name, Date, value);
		}

		public void removeField(String name)
		{
			fields.remove(name);
		}
		public boolean hasField(String name)
		{
			return fields.containsKey(name);
		}
		public Set<String> listFields()
		{
			return fields.keySet();
		}
		public void setField(String name, Object value)
		{
			fields.get(name).value = value;
		}
		public Object getField(String name, Object value)
		{
			DynamicRecordField drf = fields.get(name);
			if (drf != null) {
				return drf.value;
			}
			return null;
		}
	}

	public static class DynamicRecordPacker extends BasePacker
	{
		protected Map<Integer, BasePacker> packersMap;
		private int id;
		
		public DynamicRecordPacker(int id, Map<Integer, BasePacker> packersMap)
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
			DynamicRecord dr = (DynamicRecord)obj;
			if (dr == null) {
				Int32.pack(0, stream);
			}
			else {
				Int32.pack(dr.fields.size(), stream);
				for(Map.Entry<String, DynamicRecordField> e : dr.fields.entrySet()) {
					DynamicRecordField drf = e.getValue();
					Str.pack(e.getKey(), stream);
					Int32.pack(drf.packer.getId(), stream);
					drf.packer.pack(drf.value, stream);
				}
			}
		}
		
		public Object unpack(InputStream stream) throws IOException
		{
			int length = (Integer) Int32.unpack(stream);
			DynamicRecord dr = new DynamicRecord(length);
			for (int i = 0; i < length; i++) {
				String name = (String)Str.unpack(stream);
				Integer packerid = (Integer)Int32.unpack(stream);
				BasePacker packer = getPacker(packerid);
				Object value = packer.unpack(stream);
				dr.addField(name, packer, value);
			}
			return dr;
		}
		
		protected BasePacker getPacker(Integer id) throws UnknownPackerId
		{
			switch(id)
			{
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
				default:
					if (packersMap == null) {
						throw new UnknownPackerId("unknown packer id " + id);
					}
					BasePacker packer = (BasePacker)packersMap.get(id);
					if (packer == null) {
						throw new UnknownPackerId("unknown packer id " + id);
					}
					return packer;
			}
		}
	}
}













