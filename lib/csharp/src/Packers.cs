using System;
using System.Collections;
using System.Text;
using System.Net;
using System.Net.Sockets;
using System.IO;
using Agnos.Transports;


namespace Agnos
{
	public static class Packers
	{
		public abstract class BasePacker
		{
			public abstract void pack(object  obj, Stream stream);
            public abstract object unpack(Stream stream);

            public void pack(object obj, ITransport transport)
            {
                pack(obj, transport.GetStream());
            }

            public object unpack(ITransport transport)
            {
                return unpack(transport.GetStream());
            }

            protected static void _write(Stream stream, byte[] buf)
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

            protected static void _read(Stream stream, byte[] buf)
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
        }

		/////////////////////////////////////////////////////////////////////
		
		public class _MockupPacker : BasePacker
		{
			internal _MockupPacker(){}
			
            public override void pack(object obj, Stream stream)
			{
			}
            public override object unpack(Stream stream)
			{
				return null;
			}
		}
		
		public static _MockupPacker MockupPacker = new _MockupPacker();

        /////////////////////////////////////////////////////////////////////

		public class _Int8 : BasePacker
		{
			private byte[] buffer = new byte[1];
			
			internal _Int8(){}

			public override void pack(object obj, Stream stream)
			{
				if (obj == null) {
					pack((byte)0, stream);
				}
				else {
					pack((byte)obj, stream);
				}
			}

            public void pack(byte val, Stream stream)
			{
				buffer[0] = val;
				_write(stream, buffer);
			}

            public override object unpack(Stream stream)
			{
				_read(stream, buffer);
				return buffer[0];
			}
		}

		public static _Int8 Int8 = new _Int8();

        /////////////////////////////////////////////////////////////////////
	
		public class _Bool : BasePacker
		{
			internal _Bool(){}


            public override void pack(object obj, Stream stream)
			{
				if (obj == null) {
					pack(false, stream);
				}
				else {
					pack((bool)obj, stream);
				}
			}
			
			public void pack(bool val, Stream stream)
			{
				if (val) {
					Int8.pack((byte)1, stream);
				}
				else {
					Int8.pack((byte)1, stream);
				}
			}

            public override object unpack(Stream stream)
			{
				return ((byte)Int8.unpack(stream)) != 0;
			}
		}
	
		public static _Bool	Bool	= new _Bool();

        /////////////////////////////////////////////////////////////////////

		public class _Int16 : BasePacker
		{
			private byte[]	buffer	= new byte[2];

			internal _Int16(){}

            public override void pack(object obj, Stream stream)
			{
				if (obj == null) {
					pack((short)0, stream);
				}
				else {
					pack((short)obj, stream);
				}
			}
			
			public void pack(short val, Stream stream)
			{
				buffer[0] = (byte) ((val >> 8) & 0xff);
				buffer[1] = (byte) ((val) & 0xFF);
				_write(stream, buffer);
			}

            public override object unpack(Stream stream)
			{
				_read(stream, buffer);
				return (short)((buffer[0] & 0xff) << 8 | (buffer[1] & 0xff));
			}
		}
	
		public static _Int16	Int16 = new _Int16();

        /////////////////////////////////////////////////////////////////////

		public class _Int32 : BasePacker
		{
			private byte[]	buffer	= new byte[4];
	
			internal _Int32(){}

            public override void pack(object obj, Stream stream)
			{
				if (obj == null) {
					pack((int)0, stream);
				}
				else {
					pack((int)obj, stream);
				}
			}
			
			public void pack(int val, Stream stream)
			{
				buffer[0] = (byte) ((val >> 24) & 0xff);
				buffer[1] = (byte) ((val >> 16) & 0xff);
				buffer[2] = (byte) ((val >> 8) & 0xff);
				buffer[3] = (byte) ((val) & 0xFF);
				_write(stream, buffer);
			}

            public override object unpack(Stream stream)
			{
				_read(stream, buffer);
				return ((int)(buffer[0] & 0xff) << 24) | 
					   ((int)(buffer[1] & 0xff) << 16) |
					   ((int)(buffer[2] & 0xff) << 8)  |
					   ((int)(buffer[3] & 0xff))       ;
			}
		}
	
		public static _Int32	Int32 = new _Int32();

        /////////////////////////////////////////////////////////////////////

		public class _Int64 : BasePacker
		{
			private byte[]	buffer	= new byte[8];

			internal _Int64(){}

            public override void pack(object obj, Stream stream)
			{
				if (obj == null) {
					pack((long)0, stream);
				}
				else {
					pack((long)obj, stream);
				}
			}
			
			public void pack(long val, Stream stream)
			{
				buffer[0] = (byte) ((val >> 56) & 0xff);
				buffer[1] = (byte) ((val >> 48) & 0xff);
				buffer[2] = (byte) ((val >> 40) & 0xff);
				buffer[3] = (byte) ((val >> 32) & 0xff);
				buffer[4] = (byte) ((val >> 24) & 0xff);
				buffer[5] = (byte) ((val >> 16) & 0xff);
				buffer[6] = (byte) ((val >> 8)  & 0xff);
				buffer[7] = (byte) (val         & 0xff);
				_write(stream, buffer);
			}

            public override object unpack(Stream stream)
			{
				_read(stream, buffer);
				return (((long)(buffer[0] & 0xff)) << 56) |
					   (((long)(buffer[1] & 0xff)) << 48) |
					   (((long)(buffer[2] & 0xff)) << 40) |
					   (((long)(buffer[3] & 0xff)) << 32) |
					   (((long)(buffer[4] & 0xff)) << 24) |
					   (((long)(buffer[5] & 0xff)) << 16) |
					   (((long)(buffer[6] & 0xff)) << 8 ) |
					   (((long)(buffer[7] & 0xff))      ) ;
			}
		}
	
		public static _Int64	Int64	= new _Int64();

        /////////////////////////////////////////////////////////////////////
        
        public interface ISerializer
        {
            long store(object obj);
            object load(long id);
        }

        public class ObjRef : BasePacker
        {
            ISerializer serializer;

            public ObjRef(ISerializer serializer) 
            {
                this.serializer = serializer;
            }

            public override void pack(object obj, Stream stream)
            {
                Int64.pack(serializer.store(obj), stream);
            }

            public override object unpack(Stream stream)
            {
                return serializer.load((long)Int64.unpack(stream));
            }
        }

        /////////////////////////////////////////////////////////////////////

        public class _Float : BasePacker
		{
			internal _Float(){}

            public override void pack(object obj, Stream stream)
			{
				if (obj == null) {
					pack(0.0, stream);
				}
				else {
					pack((double)obj, stream);
				}
			}
			
			public void pack(double val, Stream stream)
			{
				Int64.pack(BitConverter.DoubleToInt64Bits(val), stream);
			}

            public override object unpack(Stream stream)
			{
				return BitConverter.Int64BitsToDouble((long)Int64.unpack(stream));
			}
		}
	
		public static _Float	Float	= new _Float();

        /////////////////////////////////////////////////////////////////////

        public class _Buffer : BasePacker
		{
			internal _Buffer(){}

            public override void pack(object obj, Stream stream)
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

            public override object unpack(Stream stream)
			{
				int length = (int)Int32.unpack(stream);
				byte[] buf = new byte[length];
				_read(stream, buf);
				return buf;
			}
		}
	
		public static _Buffer	Buffer	= new _Buffer();

        /////////////////////////////////////////////////////////////////////

        public class _Date : BasePacker
		{
			private static DateTime epoch = new DateTime(1970, 1, 1, 0, 0, 0, DateTimeKind.Utc);

			internal _Date(){}

            public override void pack(object obj, Stream stream)
			{
				DateTime val = ((DateTime)obj).ToUniversalTime();
				long timestamp = (val - epoch).Ticks / 10000;
				Int64.pack(timestamp, stream);
			}
	
			public override object unpack(Stream stream)
			{
				//long timestamp = (long)Int64.unpack(stream);
				Int64.unpack(stream);
				return DateTime.Now;
				//return new DateTime(timestamp * 10000, DateTimeKind.Local);
			}
		}
	
		public static _Date	Date	= new _Date();

        /////////////////////////////////////////////////////////////////////

        public class _Str : BasePacker
		{
			private static UTF8Encoding utf8 = new UTF8Encoding();
			
			internal _Str(){}
			
			public override void pack(object obj, Stream stream)
			{
				if (obj == null) {
					Buffer.pack(null, stream);
				}
				else {
					 Buffer.pack(utf8.GetBytes((string)obj), stream);
				}
			}
	
			public override object unpack(Stream stream)
			{
				byte[] buf = (byte[])Buffer.unpack(stream);
				return utf8.GetString(buf);
			}
		}
	
		public static _Str	Str	= new _Str();

        /////////////////////////////////////////////////////////////////////

        public class ListOf : BasePacker
		{
			private BasePacker	type;
	
			public ListOf(BasePacker type)
			{
				this.type = type;
			}
	
			public override void pack(object obj, Stream stream)
			{
				if (obj == null) {
					Int32.pack(0, stream);
				}
				else {
					IList val = (IList)obj;
					Int32.pack(val.Count, stream);
					foreach (object obj2 in val) {
						type.pack(obj2, stream);
					}
				}
			}
	
			public override object unpack(Stream stream)
			{
				int length = (int)Int32.unpack(stream);
				ArrayList arr = new ArrayList(length);
				for (int i = 0; i < length; i++) {
					arr.Add(type.unpack(stream));
				}
				return arr;
			}
		}

        /////////////////////////////////////////////////////////////////////

        public class MapOf : BasePacker
		{
			private BasePacker	keytype;
			private BasePacker	valtype;
	
			public MapOf(BasePacker keytype, BasePacker valtype)
			{
				this.keytype = keytype;
				this.valtype = valtype;
			}
	
			public override void pack(object obj, Stream stream)
			{
				if (obj == null) {
					Int32.pack(0, stream);
				}
				else {
					IDictionary val = (IDictionary)obj;
					Int32.pack(val.Count, stream);
					foreach (DictionaryEntry item in val) {
						keytype.pack(item.Key, stream);
						valtype.pack(item.Value, stream);
					}
				}
			}
	
			public override object unpack(Stream stream)
			{
				int length = (int)Int32.unpack(stream);
				Hashtable map = new Hashtable(length);
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
