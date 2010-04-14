package agnos;

import java.io.*;
import java.util.*;

public class Packers
{
	public interface IPacker
	{
		public void pack(Object obj, OutputStream stream) throws IOException;

		public Object unpack(InputStream stream) throws IOException;
	}
	
	/*private static String repr(byte[] buffer)
	{
		StringBuilder sb = new StringBuilder(buffer.length);
		int b;
		String s;
		
		for (int i = 0; i < buffer.length; i++) {
			b = buffer[i] & 0xff;
			if (b >= 32 && b <= 127) {
				sb.append((char)b);
			}
			else {
				s = Integer.toString(b, 16);
				if (s.length() == 1) {
					s = "0" + s;
				}
				sb.append("\\x" + s);
			}
		}
		return sb.toString();
	}*/

	protected static void _write(OutputStream stream, byte[] buffer)
			throws IOException
	{
		//System.out.println("W: " + repr(buffer));
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
		
		//System.out.println("R: " + repr(buffer));
	}

	public static class _Int8 implements IPacker
	{
		private byte[]	buffer	= new byte[1];

		public void pack(Object obj, OutputStream stream) throws IOException
		{
			if (obj == null) {
				buffer[0] = 0;
			}
			else {
				buffer[0] = ((Number)obj).byteValue();
			}
			_write(stream, buffer);
		}

		public Object unpack(InputStream stream) throws IOException
		{
			_read(stream, buffer);
			return new Byte(buffer[0]);
		}
	}

	public static _Int8	Int8	= new _Int8();

	public static class _Bool implements IPacker
	{
		public void pack(Object obj, OutputStream stream) throws IOException
		{
			Int8.pack(new Byte((byte)(((Boolean)obj)?1:0)), stream);
		}

		public Object unpack(InputStream stream) throws IOException
		{
			return new Boolean(((Byte) Int8.unpack(stream)) != 0);
		}
	}

	public static _Bool	Bool	= new _Bool();

	public static class _Int16 implements IPacker
	{
		private byte[]	buffer	= new byte[2];

		public void pack(Object obj, OutputStream stream) throws IOException
		{
			if (obj == null) {
				buffer[0] = 0;
				buffer[1] = 0;
			}
			else {
				short val = ((Number)obj).shortValue();
				buffer[0] = (byte) ((val >> 8) & 0xff);
				buffer[1] = (byte) ((val) & 0xFF);
			}
			_write(stream, buffer);
		}

		public Object unpack(InputStream stream) throws IOException
		{
			_read(stream, buffer);
			return new Short((short) ((buffer[0] & 0xff) << 8 | (buffer[1] & 0xff)));
		}
	}

	public static _Int16	Int16	= new _Int16();

	public static class _Int32 implements IPacker
	{
		private byte[]	buffer	= new byte[4];

		public void pack(Object obj, OutputStream stream) throws IOException
		{
			if (obj == null) {
				buffer[0] = 0;
				buffer[1] = 0;
				buffer[2] = 0;
				buffer[3] = 0;
			}
			else {
				int val = ((Number)obj).intValue();
				buffer[0] = (byte) ((val >> 24) & 0xff);
				buffer[1] = (byte) ((val >> 16) & 0xff);
				buffer[2] = (byte) ((val >> 8) & 0xff);
				buffer[3] = (byte) ((val) & 0xFF);
			}
			_write(stream, buffer);
		}

		public Object unpack(InputStream stream) throws IOException
		{
			_read(stream, buffer);
			return new Integer(((buffer[0] & 0xff) << 24 | (buffer[1] & 0xff) << 16
					| (buffer[2] & 0xff) << 8 | (buffer[3] & 0xff)));
		}
	}

	public static _Int32	Int32	= new _Int32();

	public static class _Int64 implements IPacker
	{
		private byte[]	buffer	= new byte[8];

		public void pack(Object obj, OutputStream stream) throws IOException
		{
			if (obj == null) {
				buffer[0] = 0;
				buffer[1] = 0;
				buffer[2] = 0;
				buffer[3] = 0;
				buffer[4] = 0;
				buffer[5] = 0;
				buffer[6] = 0;
				buffer[7] = 0;
			}
			else {
				long val = ((Number)obj).longValue();
				buffer[0] = (byte) ((val >> 56) & 0xff);
				buffer[1] = (byte) ((val >> 48) & 0xff);
				buffer[2] = (byte) ((val >> 40) & 0xff);
				buffer[3] = (byte) ((val >> 32) & 0xff);
				buffer[4] = (byte) ((val >> 24) & 0xff);
				buffer[5] = (byte) ((val >> 16) & 0xff);
				buffer[6] = (byte) ((val >> 8) & 0xff);
				buffer[7] = (byte) ((val) & 0xFF);
			}
			_write(stream, buffer);
		}

		public Object unpack(InputStream stream) throws IOException
		{
			_read(stream, buffer);
			return new Long((long) ((buffer[0] & 0xff) << 56 | 
					(buffer[1] & 0xff) << 48 | (buffer[2] & 0xff) << 40 | 
					(buffer[3] & 0xff) << 32 | (buffer[4] & 0xff) << 24 |
					(buffer[5] & 0xff) << 16 | (buffer[6] & 0xff) << 8 | 
					(buffer[7]  & 0xff)));
		}
	}

	public static _Int64	Int64	= new _Int64();
	public static _Int64	ObjRef	= Int64;

	public static class _Float implements IPacker
	{
		public void pack(Object obj, OutputStream stream) throws IOException
		{
			if (obj == null) {
				Int64.pack(new Long(0), stream);
			}
			else {
				Int64.pack(Double.doubleToLongBits(((Number)obj).doubleValue()), stream);
			}
		}

		public Object unpack(InputStream stream) throws IOException
		{
			return new Double(Double.longBitsToDouble((Long) (Int64
					.unpack(stream))));
		}
	}

	public static _Float	Float	= new _Float();

	public static class _Buffer implements IPacker
	{
		public void pack(Object obj, OutputStream stream) throws IOException
		{
			if (obj == null) {
				Int32.pack(new Integer(0), stream);
			}
			else {
				byte[] val = (byte[]) obj;
				Int32.pack(new Integer(val.length), stream);
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

	public static _Buffer	Buffer	= new _Buffer();

	public static class _Date implements IPacker
	{
		public void pack(Object obj, OutputStream stream) throws IOException
		{
			Int64.pack(new Long(((Date) obj).getTime()), stream);
		}

		public Object unpack(InputStream stream) throws IOException
		{
			return new Date((Long) Int64.unpack(stream));
		}
	}

	public static _Date	Date	= new _Date();

	public static class _Str implements IPacker
	{
		private static final String	encoding	= "UTF-8";

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

	public static _Str	Str	= new _Str();

	public static class ListOf implements IPacker
	{
		private IPacker	type;

		public ListOf(IPacker type)
		{
			this.type = type;
		}

		public void pack(Object obj, OutputStream stream) throws IOException
		{
			if (obj == null) {
				Int32.pack(new Integer(0), stream);
			}
			else {
				List val = (List) obj;
				Int32.pack(new Integer(val.size()), stream);

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

	public static class MapOf implements IPacker
	{
		private IPacker	keytype;
		private IPacker	valtype;

		public MapOf(IPacker keytype, IPacker valtype)
		{
			this.keytype = keytype;
			this.valtype = valtype;
		}

		public void pack(Object obj, OutputStream stream) throws IOException
		{
			if (obj == null) {
				Int32.pack(new Integer(0), stream);
			}
			else {
				Map val = (Map) obj;
				Int32.pack(new Integer(val.size()), stream);

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

}
