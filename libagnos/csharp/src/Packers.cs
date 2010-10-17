using System;
using System.Collections;
using System.Collections.Generic;
using System.Text;
using System.Net;
using System.Net.Sockets;
using System.IO;
using Agnos.Transports;


namespace Agnos
{
	public static class Packers
	{
		public const int CUSTOM_PACKER_ID_BASE = 2000;
	
		public class UnknownPackerId : ProtocolError
		{
			public UnknownPackerId(String message) : base(message) 
			{
			}
		}
		
		/////////////////////////////////////////////////////////////////////

		public abstract class AbstractPacker
		{
			public abstract void pack (object obj, Stream stream);
			public abstract object unpack (Stream stream);
			public abstract int getId ();

			public void pack (object obj, ITransport transport)
			{
				pack (obj, transport.GetStream ());
			}

			public object unpack (ITransport transport)
			{
				return unpack (transport.GetStream ());
			}

			protected static void _write (Stream stream, byte[] buf)
			{
				try {
					stream.Write (buf, 0, buf.Length);
				} catch (IOException ex) {
					throw new EndOfStreamException ("write error", ex);
				} catch (SocketException ex) {
					throw new EndOfStreamException ("write error", ex);
				}
			}

			protected static void _read (Stream stream, byte[] buf)
			{
				int total_got = 0;
				int got;
				
				try {
					while (total_got < buf.Length) {
						got = stream.Read (buf, total_got, buf.Length - total_got);
						total_got += got;
						if (got <= 0 && total_got < buf.Length) {
							throw new EndOfStreamException ("premature end of stream detected");
						}
					}
				} catch (IOException ex) {
					throw new EndOfStreamException ("read error", ex);
				} catch (SocketException ex) {
					throw new EndOfStreamException ("read error", ex);
				}
			}
		}

		/////////////////////////////////////////////////////////////////////

		public sealed class _Int8 : AbstractPacker
		{
			private byte[] buffer = new byte[1];

			internal _Int8 ()
			{
			}
			
			public override int getId()
			{
				return 1;
			}

			public override void pack (object obj, Stream stream)
			{
				if (obj == null) {
					pack ((byte)0, stream);
				} else {
					pack ((byte)obj, stream);
				}
			}

			public void pack (byte val, Stream stream)
			{
				buffer[0] = val;
				_write (stream, buffer);
			}

			public override object unpack (Stream stream)
			{
				_read (stream, buffer);
				return buffer[0];
			}
		}

		public static readonly _Int8 Int8 = new _Int8 ();

		/////////////////////////////////////////////////////////////////////

        public sealed class _Bool : AbstractPacker
		{
			internal _Bool ()
			{
			}

			public override int getId()
			{
				return 2;
			}

			public override void pack (object obj, Stream stream)
			{
				if (obj == null) {
					pack (false, stream);
				} else {
					pack ((bool)obj, stream);
				}
			}

			public void pack (bool val, Stream stream)
			{
				if (val) {
					Int8.pack ((byte)1, stream);
				} else {
					Int8.pack ((byte)1, stream);
				}
			}

			public override object unpack (Stream stream)
			{
				return ((byte)Int8.unpack (stream)) != 0;
			}
		}

		public static readonly _Bool Bool = new _Bool ();

		/////////////////////////////////////////////////////////////////////

        public sealed class _Int16 : AbstractPacker
		{
			private byte[] buffer = new byte[2];

			internal _Int16 ()
			{
			}
			
			public override int getId()
			{
				return 3;
			}

			public override void pack (object obj, Stream stream)
			{
				if (obj == null) {
					pack ((short)0, stream);
				} else {
					pack ((short)obj, stream);
				}
			}

			public void pack (short val, Stream stream)
			{
				buffer[0] = (byte)((val >> 8) & 0xff);
				buffer[1] = (byte)((val) & 0xff);
				_write (stream, buffer);
			}

			public override object unpack (Stream stream)
			{
				_read (stream, buffer);
				return (short)((buffer[0] & 0xff) << 8 | (buffer[1] & 0xff));
			}
		}

		public static readonly _Int16 Int16 = new _Int16 ();

		/////////////////////////////////////////////////////////////////////

        public sealed class _Int32 : AbstractPacker
		{
			private byte[] buffer = new byte[4];

			internal _Int32 ()
			{
			}

			public override int getId()
			{
				return 4;
			}
			
			public override void pack (object obj, Stream stream)
			{
				if (obj == null) {
					pack ((int)0, stream);
				} else {
					pack ((int)obj, stream);
				}
			}

			public void pack (int val, Stream stream)
			{
				buffer[0] = (byte)((val >> 24) & 0xff);
				buffer[1] = (byte)((val >> 16) & 0xff);
				buffer[2] = (byte)((val >> 8) & 0xff);
				buffer[3] = (byte)((val) & 0xff);
				_write (stream, buffer);
			}

			public override object unpack (Stream stream)
			{
				_read (stream, buffer);
				return ((int)(buffer[0] & 0xff) << 24) | 
						((int)(buffer[1] & 0xff) << 16) | 
						((int)(buffer[2] & 0xff) << 8) | 
						((int)(buffer[3] & 0xff));
			}
		}

		public static readonly _Int32 Int32 = new _Int32 ();

		/////////////////////////////////////////////////////////////////////

        public sealed class _Int64 : AbstractPacker
		{
			private byte[] buffer = new byte[8];

			internal _Int64 ()
			{
			}

			public override int getId()
			{
				return 5;
			}
			
			public override void pack (object obj, Stream stream)
			{
				if (obj == null) {
					pack ((long)0, stream);
				} else {
					pack ((long)obj, stream);
				}
			}

			public void pack (long val, Stream stream)
			{
				buffer[0] = (byte)((val >> 56) & 0xff);
				buffer[1] = (byte)((val >> 48) & 0xff);
				buffer[2] = (byte)((val >> 40) & 0xff);
				buffer[3] = (byte)((val >> 32) & 0xff);
				buffer[4] = (byte)((val >> 24) & 0xff);
				buffer[5] = (byte)((val >> 16) & 0xff);
				buffer[6] = (byte)((val >> 8) & 0xff);
				buffer[7] = (byte)(val & 0xff);
				_write (stream, buffer);
			}

			public override object unpack (Stream stream)
			{
				_read (stream, buffer);
				return (((long)(buffer[0] & (uint)0xff)) << 56) | 
						(((long)(buffer[1] & (uint)0xff)) << 48) | 
						(((long)(buffer[2] & (uint)0xff)) << 40) | 
						(((long)(buffer[3] & (uint)0xff)) << 32) | 
						(((long)(buffer[4] & (uint)0xff)) << 24) | 
						(((long)(buffer[5] & (uint)0xff)) << 16) | 
						(((long)(buffer[6] & (uint)0xff)) << 8) | 
						(((long)(buffer[7] & (uint)0xff)));
			}
		}

		public static readonly _Int64 Int64 = new _Int64 ();

		/////////////////////////////////////////////////////////////////////

		public interface ISerializer
		{
			long store (object obj);
			object load (long id);
		}

        public class ObjRef : AbstractPacker
		{
			protected readonly ISerializer serializer;
            protected readonly int id;

			public ObjRef (int id, ISerializer serializer)
			{
				this.serializer = serializer;
				this.id = id;
			}

			public override int getId()
			{
				return id;
			}
			
			public override void pack (object obj, Stream stream)
			{
				Int64.pack (serializer.store (obj), stream);
			}

			public override object unpack (Stream stream)
			{
				return serializer.load ((long)Int64.unpack (stream));
			}
		}

		/////////////////////////////////////////////////////////////////////

        public sealed class _Float : AbstractPacker
		{
			internal _Float ()
			{
			}

			public override int getId()
			{
				return 6;
			}
			
			public override void pack (object obj, Stream stream)
			{
				if (obj == null) {
					pack (0.0, stream);
				} else {
					pack ((double)obj, stream);
				}
			}

			public void pack (double val, Stream stream)
			{
				Int64.pack (BitConverter.DoubleToInt64Bits (val), stream);
			}

			public override object unpack (Stream stream)
			{
				return BitConverter.Int64BitsToDouble ((long)Int64.unpack (stream));
			}
		}

		public static readonly _Float Float = new _Float ();

		/////////////////////////////////////////////////////////////////////

        public sealed class _Buffer : AbstractPacker
		{
			internal _Buffer ()
			{
			}

			public override int getId()
			{
				return 7;
			}
			
			public override void pack (object obj, Stream stream)
			{
				if (obj == null) {
					Int32.pack (0, stream);
				} else {
					byte[] val = (byte[])obj;
					Int32.pack (val.Length, stream);
					_write (stream, val);
				}
			}

			public override object unpack (Stream stream)
			{
				int length = (int)Int32.unpack (stream);
				byte[] buf = new byte[length];
				_read (stream, buf);
				return buf;
			}
		}

		public static readonly _Buffer Buffer = new _Buffer ();

		/////////////////////////////////////////////////////////////////////

        public sealed class _Date : AbstractPacker
		{
			internal _Date ()
			{
			}

			public override int getId()
			{
				return 8;
			}
			
			public override void pack (object obj, Stream stream)
			{
				long timestamp = ((DateTime)obj).ToUniversalTime().Ticks / 10;
				Int64.pack (timestamp, stream);
			}

			public override object unpack (Stream stream)
			{
				long timestamp = (long)Int64.unpack(stream);
				return new DateTime(timestamp * 10, DateTimeKind.Utc);
			}
		}

		public static readonly _Date Date = new _Date ();

		/////////////////////////////////////////////////////////////////////

        public sealed class _Str : AbstractPacker
		{
            private readonly static UTF8Encoding utf8 = new UTF8Encoding();

			internal _Str ()
			{
			}

			public override int getId()
			{
				return 9;
			}
			
			public override void pack (object obj, Stream stream)
			{
				if (obj == null) {
					Buffer.pack (null, stream);
				} else {
					Buffer.pack (utf8.GetBytes ((string)obj), stream);
				}
			}

			public override object unpack (Stream stream)
			{
				byte[] buf = (byte[])Buffer.unpack (stream);
				return utf8.GetString (buf);
			}
		}

		public static readonly _Str Str = new _Str ();

		/////////////////////////////////////////////////////////////////////

		public class ListOf<T> : AbstractPacker
		{
            protected readonly AbstractPacker type;
            protected readonly int id;

			public ListOf (int id, AbstractPacker type)
			{
				this.type = type;
				this.id = id;
			}

			public override int getId()
			{
				return id;
			}
			
			public override void pack (object obj, Stream stream)
			{
				if (obj == null) {
					Int32.pack (0, stream);
				} 
				else if (obj is T[]) {
					T[] val = (T[])obj;
					Int32.pack (val.Length, stream);
					foreach (T item in val) {
						type.pack (item, stream);
					}
				}
				else {
					IList<T> coll = (IList<T>)obj;
					Int32.pack (coll.Count, stream);
					foreach (T item in coll) {
						type.pack (item, stream);
					}
				}
			}

			public override object unpack (Stream stream)
			{
				int length = (int)Int32.unpack (stream);
				List<T> lst = new List<T> (length);
				for (int i = 0; i < length; i++) {
					lst.Add ((T)(type.unpack (stream)));
				}
				return lst;
			}
		}

		public static readonly ListOf<byte> listOfInt8 = new ListOf<byte>(800, Int8);
		public static readonly ListOf<bool> listOfBool = new ListOf<bool>(801, Bool);
		public static readonly ListOf<short> listOfInt16 = new ListOf<short>(802, Int16);
		public static readonly ListOf<int> listOfInt32 = new ListOf<int>(803, Int32);
		public static readonly ListOf<long> listOfInt64 = new ListOf<long>(804, Int64);
		public static readonly ListOf<double> listOfFloat = new ListOf<double>(805, Float);
		public static readonly ListOf<byte[]> listOfBuffer = new ListOf<byte[]>(806, Buffer);
		public static readonly ListOf<DateTime> listOfDate = new ListOf<DateTime>(807, Date);
		public static readonly ListOf<string> listOfStr = new ListOf<string>(808, Str);
		
		/////////////////////////////////////////////////////////////////////

		public class SetOf<T> : AbstractPacker
		{
            protected readonly AbstractPacker type;
            protected readonly int id;

			public SetOf (int id, AbstractPacker type)
			{
				this.type = type;
				this.id = id;
			}

			public override int getId()
			{
				return id;
			}
			
			public override void pack (object obj, Stream stream)
			{
				if (obj == null) {
					Int32.pack (0, stream);
				} 
				else {
					ICollection<T> coll = (ICollection<T>)obj;
					Int32.pack (coll.Count, stream);
					foreach (T item in coll) {
						type.pack (item, stream);
					}
				}
			}

			public override object unpack (Stream stream)
			{
				int length = (int)Int32.unpack (stream);
				HashSet<T> obj = new HashSet<T> ();
				for (int i = 0; i < length; i++) {
					obj.Add ((T)(type.unpack (stream)));
				}
				return obj;
			}
		}

		public static readonly SetOf<byte> setOfInt8 = new SetOf<byte>(820, Int8);
		public static readonly SetOf<bool> setOfBool = new SetOf<bool>(821, Bool);
		public static readonly SetOf<short> setOfInt16 = new SetOf<short>(822, Int16);
		public static readonly SetOf<int> setOfInt32 = new SetOf<int>(823, Int32);
		public static readonly SetOf<long> setOfInt64 = new SetOf<long>(824, Int64);
		public static readonly SetOf<double> setOfFloat = new SetOf<double>(825, Float);
		public static readonly SetOf<byte[]> setOfBuffer = new SetOf<byte[]>(826, Buffer);
		public static readonly SetOf<DateTime> setOfDate = new SetOf<DateTime>(827, Date);
		public static readonly SetOf<string> setOfStr = new SetOf<string>(828, Str);
		
		/////////////////////////////////////////////////////////////////////

		public class MapOf<K, V> : AbstractPacker
		{
            protected readonly AbstractPacker keytype;
            protected readonly AbstractPacker valtype;
            protected readonly int id;

			public MapOf (int id, AbstractPacker keytype, AbstractPacker valtype)
			{
				this.keytype = keytype;
				this.valtype = valtype;
				this.id = id;
			}

			public override int getId()
			{
				return id;
			}
			
			public override void pack (object obj, Stream stream)
			{
				if (obj == null) {
					Int32.pack (0, stream);
				} else {
					IDictionary coll = (IDictionary)obj;
					Int32.pack (coll.Count, stream);
					foreach (DictionaryEntry item in coll) {
						keytype.pack (item.Key, stream);
						valtype.pack (item.Value, stream);
					}
				}
			}

			public override object unpack (Stream stream)
			{
				int length = (int)Int32.unpack (stream);
				Dictionary<K, V> map = new Dictionary<K, V>(length);
				for (int i = 0; i < length; i++) {
					K k = (K)(keytype.unpack (stream));
					V v = (V)(valtype.unpack (stream));
					map.Add (k, v);
				}
				return map;
			}
		}

		public static readonly MapOf<int, int> mapOfInt32Int32 = new MapOf<int, int> (850, Int32, Int32);
		public static readonly MapOf<int, string> mapOfInt32Str = new MapOf<int, string> (851, Int32, Str);
		public static readonly MapOf<string, int> mapOfStrInt32 = new MapOf<string, int> (852, Str, Int32);
		public static readonly MapOf<string, string> mapOfStrStr = new MapOf<string, string> (853, Str, Str);

		// ////////////////////////////////////////////////////////////////////////

		public class HeteroMapPacker : AbstractPacker
		{
			protected readonly IDictionary<int, AbstractPacker> packersMap;
			protected int id;

			public HeteroMapPacker (int id, IDictionary<int, AbstractPacker> packersMap)
			{
				this.id = id;
				this.packersMap = packersMap;
			}

			public override int getId()
			{
				return id;
			}

			public override void pack (Object obj, Stream stream)
			{
				HeteroMap map = (HeteroMap)obj;
				if (map == null) {
					Int32.pack (0, stream);
				} 
				else {
					Int32.pack (map.Count, stream);
					foreach (DictionaryEntry e in map) {
						AbstractPacker keypacker = map.getKeyPacker(e.Key);
						AbstractPacker valpacker = map.getValuePacker(e.Key);
						
						Int32.pack (keypacker.getId (), stream);
						keypacker.pack (e.Key, stream);
						
						Int32.pack (valpacker.getId (), stream);
						valpacker.pack (e.Value, stream);
					}
				}
			}

			public override Object unpack (Stream stream)
			{
				int length = (int)Int32.unpack (stream);
				HeteroMap map = new HeteroMap (length);
				
				for (int i = 0; i < length; i++) {
					int keypid = (int)Int32.unpack (stream);
					AbstractPacker keypacker = getPacker (keypid);
					Object key = keypacker.unpack (stream);
					
					int valpid = (int)Int32.unpack (stream);
					AbstractPacker valpacker = getPacker (valpid);
					Object val = valpacker.unpack (stream);
					
					map.Add(key, keypacker, val, valpacker);
				}
				return map;
			}

			protected AbstractPacker getPacker (int id)
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
				case 820:
					return setOfInt8;
				case 821:
					return setOfBool;
				case 822:
					return setOfInt16;
				case 823:
					return setOfInt32;
				case 824:
					return setOfInt64;
				case 825:
					return setOfFloat;
				case 826:
					return setOfBuffer;
				case 827:
					return setOfDate;
				case 828:
					return setOfStr;
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
					//	throw new UnknownPackerId ("packer id too low" + id);
					//}
					if (packersMap == null) {
						throw new UnknownPackerId ("unknown packer id " + id);
					}
					AbstractPacker packer;
					if (!packersMap.TryGetValue(id, out packer)) {
						throw new UnknownPackerId ("unknown packer id " + id);
					}
					return packer;
				}
			}
		}

		public static readonly HeteroMapPacker builtinHeteroMapPacker = new HeteroMapPacker (998, null);
	}
	
	
}
