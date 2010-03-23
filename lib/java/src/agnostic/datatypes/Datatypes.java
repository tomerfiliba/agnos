package agnostic.datatypes;

import java.io.*;
import java.util.*;


public class Datatypes
{
	public interface IDatatype
	{
		public void pack(Object obj, OutputStream stream) throws IOException;

		public Object unpack(InputStream stream) throws IOException;
	}

	public static class _Int8 implements IDatatype
	{
		public void pack(Object obj, OutputStream stream) throws IOException
		{
			stream.write((Byte) obj & 0xFF);
		}

		public Object unpack(InputStream stream) throws IOException
		{
			return new Byte((byte)stream.read());
		}
	}

	public static _Int8	Int8	= new _Int8();

	public static class _Bool implements IDatatype
	{
		public void pack(Object obj, OutputStream stream) throws IOException
		{
			Int8.pack(new Byte(((Boolean) obj) ? (byte)1 : (byte)0), stream);
		}

		public Object unpack(InputStream stream) throws IOException
		{
			return new Boolean((Byte)Int8.unpack(stream) != 0);
		}
	}

	public static _Bool	Bool	= new _Bool();

	public static class _Int16 implements IDatatype
	{
		private byte[]	buffer	= new byte[2];

		public void pack(Object obj, OutputStream stream) throws IOException
		{
			short val = (Short) obj;
			buffer[0] = (byte) ((val >> 8) & 0xff);
			buffer[1] = (byte) ((val) & 0xFF);
			stream.write(buffer);
		}

		public Object unpack(InputStream stream) throws IOException
		{
			stream.read(buffer, 0, buffer.length);
			return new Short((short)(buffer[0] << 8 | buffer[1]));
		}
	}

	public static _Int16	Int16	= new _Int16();

	public static class _Int32 implements IDatatype
	{
		private byte[]	buffer	= new byte[4];

		public void pack(Object obj, OutputStream stream) throws IOException
		{
			int val = (Integer) obj;
			buffer[0] = (byte) ((val >> 24) & 0xff);
			buffer[1] = (byte) ((val >> 16) & 0xff);
			buffer[2] = (byte) ((val >> 8) & 0xff);
			buffer[3] = (byte) ((val) & 0xFF);
			stream.write(buffer);
		}

		public Object unpack(InputStream stream) throws IOException
		{
			stream.read(buffer, 0, buffer.length);
			return new Integer((buffer[0] << 24 | buffer[1] << 16
					| buffer[2] << 8 | buffer[3]));
		}
	}

	public static _Int32	Int32	= new _Int32();

	public static class _Int64 implements IDatatype
	{
		private byte[]	buffer	= new byte[8];

		public void pack(Object obj, OutputStream stream) throws IOException
		{
			int val = (Integer) obj;
			buffer[0] = (byte) ((val >> 56) & 0xff);
			buffer[1] = (byte) ((val >> 48) & 0xff);
			buffer[2] = (byte) ((val >> 40) & 0xff);
			buffer[3] = (byte) ((val >> 32) & 0xff);
			buffer[4] = (byte) ((val >> 24) & 0xff);
			buffer[5] = (byte) ((val >> 16) & 0xff);
			buffer[6] = (byte) ((val >> 8) & 0xff);
			buffer[7] = (byte) ((val) & 0xFF);
			stream.write(buffer);
		}

		public Object unpack(InputStream stream) throws IOException
		{
			stream.read(buffer, 0, buffer.length);
			return new Long((long)(buffer[0] << 56 | buffer[1] << 48
					| buffer[2] << 40 | buffer[3] << 32 | buffer[4] << 24
					| buffer[5] << 16 | buffer[6] << 8 | buffer[7]));
		}
	}

	public static _Int64	Int64	= new _Int64();
	public static _Int64	ObjRef	= Int64;

	public static class _Float implements IDatatype
	{
		public void pack(Object obj, OutputStream stream) throws IOException
		{
			Int64.pack(Double.doubleToLongBits((Double) obj), stream);
		}

		public Object unpack(InputStream stream) throws IOException
		{
			return new Double(Double.longBitsToDouble((Long)(Int64.unpack(stream))));
		}
	}

	public static _Float	Float = new _Float();

	public static class _String implements IDatatype
	{
		public void pack(Object obj, OutputStream stream) throws IOException
		{
			String val = (String) obj;
			Int32.pack(new Integer(val.length()), stream);
			stream.write(val.getBytes("UTF-8"));
		}

		public Object unpack(InputStream stream) throws IOException
		{
			int length = (Integer)Int32.unpack(stream);
			byte[] buf = new byte[length];
			stream.read(buf, 0, length);
			return new String(buf, "UTF-8");
		}
	}

	public static _String	Str	= new _String();

	public static class _Buffer implements IDatatype
	{
		public void pack(Object obj, OutputStream stream) throws IOException
		{
			byte[] val = (byte[]) obj;
			Int32.pack(new Integer(val.length), stream);
			stream.write(val);
		}

		public Object unpack(InputStream stream) throws IOException
		{
			int length = (Integer)Int32.unpack(stream);
			byte[] buf = new byte[length];
			stream.read(buf, 0, length);
			return buf;
		}
	}

	public static _Buffer	Buffer	= new _Buffer();

	public static class ListOf implements IDatatype
	{
		private IDatatype	type;

		public ListOf(IDatatype type)
		{
			this.type = type;
		}

		public void pack(Object obj, OutputStream stream) throws IOException
		{
			List val = (List) obj;
			Int32.pack(new Integer(val.size()), stream);

			Iterator it = val.iterator();
			while (it.hasNext()) {
				type.pack(it.next(), stream);
			}
		}

		public Object unpack(InputStream stream) throws IOException
		{
			int length = (Integer)Int32.unpack(stream);
			ArrayList<Object> arr = new ArrayList<Object>(length);
			for (int i = 0; i < length; i++) {
				arr.add(type.unpack(stream));
			}
			return arr;
		}
	}

	public static class MapOf implements IDatatype
	{
		private IDatatype	keytype;
		private IDatatype	valtype;

		public MapOf(IDatatype keytype, IDatatype valtype)
		{
			this.keytype = keytype;
			this.valtype = valtype;
		}

		public void pack(Object obj, OutputStream stream) throws IOException
		{
			Map val = (Map) obj;
			Int32.pack(new Integer(val.size()), stream);
			Set s = val.entrySet();
			Iterator it = s.iterator();
			while (it.hasNext()) {
				Map.Entry m = (Map.Entry) it.next();
				keytype.pack(m.getKey(), stream);
				valtype.pack(m.getValue(), stream);
			}
		}

		public Object unpack(InputStream stream) throws IOException
		{
			int length = (Integer)Int32.unpack(stream);
			Map<Object, Object> map = new HashMap<Object, Object>(length);
			for (int i = 0; i < length; i++) {
				Object k = keytype.unpack(stream);
				Object v = valtype.unpack(stream);
				map.put(k, v);
			}
			return map;
		}
	}

	// autogenerated
	
	public static class Person
	{
		public String	name;
		public int		age;

		public Person()
		{
		}

		public Person(String name, int age)
		{
			this.name = name;
			this.age = age;
		}
		
		public void pack(OutputStream stream) throws IOException
		{
			PersonRecord.pack(this, stream);
		}
		
		public static Person unpack(InputStream stream) throws IOException
		{
			return (Person)PersonRecord.unpack(stream);
		}
	}
	
	protected static class _PersonRecord implements IDatatype
	{
		public void pack(Object obj, OutputStream stream) throws IOException
		{
			Person val = (Person)obj;
			Str.pack(val.name, stream);
			Int32.pack(val.age, stream);
		}

		public Object unpack(InputStream stream) throws IOException
		{
			return new Person((String)Str.unpack(stream), (Integer)Int32.unpack(stream));
		}
	}
	
	protected static _PersonRecord PersonRecord = new _PersonRecord();
	
	public static class Family
	{
		Person mother;
		Person father;
		
		public Family()
		{
		}

		public Family(Person mother, Person father)
		{
			this.mother = mother;
			this.father = father;
		}
		
		public void pack(OutputStream stream) throws IOException
		{
			FamilyRecord.pack(this, stream);
		}
		
		public static Family unpack(InputStream stream) throws IOException
		{
			return (Family)FamilyRecord.unpack(stream);
		}
	}

	protected static class _FamilyRecord implements IDatatype
	{
		public void pack(Object obj, OutputStream stream) throws IOException
		{
			Family val = (Family)obj;
			PersonRecord.pack(val.mother, stream);
			PersonRecord.pack(val.father, stream);
		}

		public Object unpack(InputStream stream) throws IOException
		{
			return new Family((Person)PersonRecord.unpack(stream), (Person)PersonRecord.unpack(stream));
		}
	}
	
	protected static _FamilyRecord FamilyRecord = new _FamilyRecord();
	
	
}






















