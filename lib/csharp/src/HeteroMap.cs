using System;
using System.Collections;
using System.Collections.Generic;


namespace Agnos
{
	public class HeteroMap : IDictionary
	{
		protected class FieldInfo
		{
			public Packers.AbstractPacker keypacker;
			public Packers.AbstractPacker valpacker;
			public FieldInfo(Packers.AbstractPacker keypacker, Packers.AbstractPacker valpacker)
			{
				this.keypacker = keypacker;
				this.valpacker = valpacker;
			}
		}
		protected Dictionary<object, FieldInfo> fields;
		protected Hashtable data;
		
		public HeteroMap()
		{
			fields = new Dictionary<object, FieldInfo>();
			data = new Hashtable();
		}
		public HeteroMap(int capacity)
		{
			fields = new Dictionary<object, FieldInfo>(capacity);
			data = new Hashtable(capacity);
		}
		public HeteroMap(HeteroMap other)
		{
			fields = new Dictionary<object, FieldInfo>(other.fields);
			data = new Hashtable(other.data);
		}
		
		public int Count {
			get { return data.Count;}
		}
		public bool IsReadOnly { 
			get { return false; }
		}
		public bool IsFixedSize { 
			get { return false; } 
		}
		public bool IsSynchronized { 
			get { return false; }
		}
		public ICollection Keys {
			get { return data.Keys; }
		}
		public Object SyncRoot {
			get { return data.SyncRoot; }
		}
		public ICollection Values { 
			get {return data.Values; }
		}
		
		public void Clear()
		{
			data.Clear();
			fields.Clear();
		}
		public bool Contains(Object key) 
		{
			return data.Contains(key);
		}
		public bool ContainsKey(Object key) 
		{
			return data.ContainsKey(key);
		}
		public bool ContainsValue(Object value)
		{
			return data.ContainsValue(value);
		}
		public void CopyTo(Array array, int arrayIndex)
		{
			data.CopyTo(array, arrayIndex);
		}
		public void Update(HeteroMap other)
		{
			foreach (KeyValuePair<Object, FieldInfo> e in other.fields) {
				Add(e.Key, e.Value.keypacker, other.data[e.Key], e.Value.valpacker);
			}
		}
		IEnumerator IEnumerable.GetEnumerator()
		{
			return (IEnumerator)GetEnumerator();
		}
		public IDictionaryEnumerator GetEnumerator()
		{
			return data.GetEnumerator();
		}
		public void Remove(object key)
		{
			data.Remove(key);
			fields.Remove(key);
		}
		
		protected Packers.AbstractPacker getPackerForBuiltinType(object val)
		{
			if (val is string || val is String) {
				return Packers.Str;
			}
			if (val is int || val is Int32) {
				return Packers.Int32;
			}
			if (val is long || val is Int64) {
				return Packers.Int64;
			}
			if (val is float || val is double || val is Double) {
				return Packers.Float;
			}
			if (val is byte || val is Byte) {
				return Packers.Int8;
			}
			if (val is short || val is Int16) {
				return Packers.Int16;
			}
			if (val is byte[]) {
				return Packers.Buffer;
			}
			if (val is DateTime) {
				return Packers.Date;
			}
			return null;
		}

		public void Add(Object key,	Packers.AbstractPacker keypacker, Object value, Packers.AbstractPacker valpacker)
		{
			//System.Console.Error.WriteLine("Add: {0}, {1}, {2}, {3}", key, keypacker, value, valpacker);
			if (keypacker == null || valpacker == null) {
				throw new ArgumentNullException("keypacker and valpacker cannot be null");
			}
			FieldInfo fi = null;
			if (fields.TryGetValue(key, out fi)) {
				fi.keypacker = keypacker;
				fi.valpacker = valpacker;
			}
			else {
				fields.Add(key, new FieldInfo(keypacker, valpacker));
			}
			data.Add(key, value);
		}

		public void Add(String key, String value)
		{
			Add(key, Packers.Str, value, Packers.Str);
		}
		public void Add(String key, int value)
		{
			Add(key, Packers.Str, value, Packers.Int32);
		}
		public void Add(int key, String value)
		{
			Add(key, Packers.Int32, value, Packers.Str);
		}
		public void Add(int key, int value)
		{
			Add(key, Packers.Int32, value, Packers.Int32);
		}
		
		public void Add(Object key, Object value)
		{
			Packers.AbstractPacker keypacker = getPackerForBuiltinType(key);
			Packers.AbstractPacker valpacker = getPackerForBuiltinType(value);
			if (keypacker == null) {
				keypacker = getKeyPacker(key);
			}
			if (valpacker == null) {
				valpacker = getValuePacker(key);
			}
			if (valpacker == null || keypacker == null) {
				throw new ArgumentException("cannot deduce key or value packer, use 4-argument Add()");
			}
			Add(key, keypacker, value, valpacker);
		}

		public void Add(Object key, Object value, Packers.AbstractPacker valpacker)
		{
			Packers.AbstractPacker keypacker = getPackerForBuiltinType(key);
			if (keypacker == null) {
				keypacker = getKeyPacker(key);
			}
			if (keypacker == null) {
				throw new ArgumentException("cannot deduce key packer, use 4-argument Add()");
			}
			Add(key, keypacker, value, valpacker);
		}		
		
		public bool TryGetValue(Object key, out Object value)
		{
			if (data.Contains(key)) {
				value = data[key];
				return true;
			}
			else {
				value = null;
				return false;
			}
		}
		
		public Object this[Object key] {
			get {
				return data[key];
			} 
			set {
				Add(key, value);
			}
		}
		
		public Packers.AbstractPacker getKeyPacker(Object key)
		{
			return fields[key].keypacker;
		}
		
		public Packers.AbstractPacker getValuePacker(Object key)
		{
			return fields[key].valpacker;
		}
	}
	
}
