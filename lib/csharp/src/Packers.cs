using System;
using System.Collections.Generic;
using System.Text;
using System.Net;
using System.Net.Sockets;
using System.IO;


namespace Agnos
{
	public static class Packers
	{
		public interface IPacker
		{
			void pack(object  obj, Stream stream);
			object unpack(Stream stream);
		}

		internal static void _write(Stream stream, byte[] buf)
		{
            try
            {
			    stream.Write(buf, 0, buf.Length);
            }
            catch (IOException ex)
            {
                throw new EndOfStreamException("write error", ex);
            }
            catch (SocketException ex)
            {
                throw new EndOfStreamException("write error", ex);
            }
        }

		internal static void _read(Stream stream, byte[] buf)
		{
			int total_got = 0;
			int got;

            try
            {
                while (total_got < buf.Length)
                {
                    got = stream.Read(buf, total_got, buf.Length - total_got);
                    total_got += got;
                    if (got <= 0 && total_got < buf.Length)
                    {
                        throw new EndOfStreamException("premature end of stream detected");
                    }
                }
            }
            catch (IOException ex)
            {
                throw new EndOfStreamException("read error", ex);
            }
            catch (SocketException ex)
            {
                throw new EndOfStreamException("read error", ex);
            }
        }

        /////////////////////////////////////////////////////////////////////

		public class _Int8 : IPacker
		{
			private byte[] buffer = new byte[1];
			
			internal _Int8(){}
			
			public void pack(object obj, Stream stream)
			{
				if (obj == null) {
					buffer[0] = 0;
				}
				else {
					buffer[0] = (byte)obj;
				}
				_write(stream, buffer);
			}
	
			public object unpack(Stream stream)
			{
				_read(stream, buffer);
				return buffer[0];
			}
		}

		public static _Int8 Int8 = new _Int8();

        /////////////////////////////////////////////////////////////////////
	
		public class _Bool : IPacker
		{
			internal _Bool(){}

			public void pack(object obj, Stream stream)
			{
				Int8.pack((bool)obj ? 1 : 0, stream);
			}
	
			public object unpack(Stream stream)
			{
				return ((byte)Int8.unpack(stream)) != 0;
			}
		}
	
		public static _Bool	Bool	= new _Bool();

        /////////////////////////////////////////////////////////////////////

		public class _Int16 : IPacker
		{
			private byte[]	buffer	= new byte[2];

			internal _Int16(){}

			public void pack(object obj, Stream stream)
			{
				short val = 0;
				if (obj != null) {
					obj = (short)obj;
				}
				buffer[0] = (byte) ((val >> 8) & 0xff);
				buffer[1] = (byte) ((val) & 0xFF);
				_write(stream, buffer);
			}
	
			public object unpack(Stream stream)
			{
				_read(stream, buffer);
				return (short)((buffer[0] & 0xff) << 8 | (buffer[1] & 0xff));
			}
		}
	
		public static _Int16	Int16 = new _Int16();

        /////////////////////////////////////////////////////////////////////

		public class _Int32 : IPacker
		{
			private byte[]	buffer	= new byte[4];
	
			internal _Int32(){}

			public void pack(object obj, Stream stream)
			{
				int val = 0;
				if (obj != null) {
					val = (int)obj;
				}
				buffer[0] = (byte) ((val >> 24) & 0xff);
				buffer[1] = (byte) ((val >> 16) & 0xff);
				buffer[2] = (byte) ((val >> 8) & 0xff);
				buffer[3] = (byte) ((val) & 0xFF);
				_write(stream, buffer);
			}
	
			public object unpack(Stream stream)
			{
				_read(stream, buffer);
				return (int)((buffer[0] & 0xff) << 24 | (buffer[1] & 0xff) << 16
						| (buffer[2] & 0xff) << 8 | (buffer[3] & 0xff));
			}
		}
	
		public static _Int32	Int32 = new _Int32();

        /////////////////////////////////////////////////////////////////////

		public class _Int64 : IPacker
		{
			private byte[]	buffer	= new byte[8];

			internal _Int64(){}

			public void pack(object obj, Stream stream)
			{
				long val = 0;
				if (obj != null) {
					val = (long)obj;
				}
				buffer[0] = (byte) ((val >> 56) & 0xff);
				buffer[1] = (byte) ((val >> 48) & 0xff);
				buffer[2] = (byte) ((val >> 40) & 0xff);
				buffer[3] = (byte) ((val >> 32) & 0xff);
				buffer[4] = (byte) ((val >> 24) & 0xff);
				buffer[5] = (byte) ((val >> 16) & 0xff);
				buffer[6] = (byte) ((val >> 8) & 0xff);
				buffer[7] = (byte) ((val) & 0xFF);
				_write(stream, buffer);
			}
	
			public object unpack(Stream stream)
			{
				_read(stream, buffer);
				return (long) ((buffer[0] & 0xff) << 56 | 
						(buffer[1] & 0xff) << 48 | (buffer[2] & 0xff) << 40 | 
						(buffer[3] & 0xff) << 32 | (buffer[4] & 0xff) << 24 |
						(buffer[5] & 0xff) << 16 | (buffer[6] & 0xff) << 8 | 
						(buffer[7]  & 0xff));
			}
		}
	
		public static _Int64	Int64	= new _Int64();

        /////////////////////////////////////////////////////////////////////
        
        public interface ISerializer
        {
            long store(object obj);
            object load(long id);
        }

        public class ObjRef : IPacker
        {
            ISerializer serializer;

            public ObjRef(ISerializer serializer) 
            {
                this.serializer = serializer;
            }

            public void pack(object obj, Stream stream)
            {
                Int64.pack(serializer.store(obj), stream);
            }

            public object unpack(Stream stream)
            {
                return serializer.load((long)Int64.unpack(stream));
            }
        }

        /////////////////////////////////////////////////////////////////////

        public class _Float : IPacker
		{
			internal _Float(){}

			public void pack(object obj, Stream stream)
			{
				long bits = 0;
				if (obj != null) {
					bits = BitConverter.DoubleToInt64Bits((double)obj);
				}
				Int64.pack(bits, stream);
			}
	
			public object unpack(Stream stream)
			{
				return BitConverter.Int64BitsToDouble((long)Int64.unpack(stream));
			}
		}
	
		public static _Float	Float	= new _Float();

        /////////////////////////////////////////////////////////////////////

        public class _Buffer : IPacker
		{
			internal _Buffer(){}

			public void pack(object obj, Stream stream)
			{
				if (obj == null) {
					Int32.pack(0, stream);
				}
				else {
					byte[] val = (byte[]) obj;
					Int32.pack(val.Length, stream);
					_write(stream, val);
				}
			}
	
			public object unpack(Stream stream)
			{
				int length = (int)Int32.unpack(stream);
				byte[] buf = new byte[length];
				_read(stream, buf);
				return buf;
			}
		}
	
		public static _Buffer	Buffer	= new _Buffer();

        /////////////////////////////////////////////////////////////////////

        public class _Date : IPacker
		{
			private static DateTime epoch = new DateTime(1970, 1, 1, 0, 0, 0, DateTimeKind.Utc);

			internal _Date(){}

			public void pack(object obj, Stream stream)
			{
				DateTime val = ((DateTime)obj).ToUniversalTime();
				long timestamp = (val - epoch).Ticks / 10000;
				Int64.pack(timestamp, stream);
			}
	
			public object unpack(Stream stream)
			{
				long timestamp = (long)Int64.unpack(stream);
				return DateTime.Now;
				//return new DateTime(timestamp * 10000, DateTimeKind.Local);
			}
		}
	
		public static _Date	Date	= new _Date();

        /////////////////////////////////////////////////////////////////////

        public class _Str : IPacker
		{
			private static UTF8Encoding utf8 = new UTF8Encoding();
			
			internal _Str(){}
			
			public void pack(object obj, Stream stream)
			{
				if (obj == null) {
					Buffer.pack(null, stream);
				}
				else {
					 Buffer.pack(utf8.GetBytes((string)obj), stream);
				}
			}
	
			public object unpack(Stream stream)
			{
				byte[] buf = (byte[])Buffer.unpack(stream);
				return utf8.GetString(buf);
			}
		}
	
		public static _Str	Str	= new _Str();

        /////////////////////////////////////////////////////////////////////

        public class ListOf : IPacker
		{
			private IPacker	type;
	
			public ListOf(IPacker type)
			{
				this.type = type;
			}
	
			public void pack(object obj, Stream stream)
			{
				if (obj == null) {
					Int32.pack(0, stream);
				}
				else {
					List<object> val = (List<object>)obj;
					Int32.pack(val.Count, stream);
					foreach (object obj2 in val) {
						type.pack(obj2, stream);
					}
				}
			}
	
			public object unpack(Stream stream)
			{
				int length = (int)Int32.unpack(stream);
				List<object> arr = new List<object>(length);
				for (int i = 0; i < length; i++) {
					arr.Add(type.unpack(stream));
				}
				return arr;
			}
		}

        /////////////////////////////////////////////////////////////////////

        public class MapOf : IPacker
		{
			private IPacker	keytype;
			private IPacker	valtype;
	
			public MapOf(IPacker keytype, IPacker valtype)
			{
				this.keytype = keytype;
				this.valtype = valtype;
			}
	
			public void pack(object obj, Stream stream)
			{
				if (obj == null) {
					Int32.pack(0, stream);
				}
				else {
					Dictionary<Object, Object> val = (Dictionary<Object, Object>)obj;
					Int32.pack(val.Count, stream);
					foreach (KeyValuePair<object, object> item in val) {
						keytype.pack(item.Key, stream);
						valtype.pack(item.Value, stream);
					}
				}
			}
	
			public object unpack(Stream stream)
			{
				int length = (int)Int32.unpack(stream);
				Dictionary<Object, Object> map = new Dictionary<Object, Object>(length);
				for (int i = 0; i < length; i++) {
					object k = keytype.unpack(stream);
					object v = valtype.unpack(stream);
					map.Add(k, v);
				}
				return map;
			}
		}
	}

}