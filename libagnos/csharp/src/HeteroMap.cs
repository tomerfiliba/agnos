//////////////////////////////////////////////////////////////////////////////
// Part of the Agnos RPC Framework
//    http://agnos.sourceforge.net
//
// Copyright 2011, International Business Machines Corp.
//                 Author: Tomer Filiba (tomerf@il.ibm.com)
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//    http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.
//////////////////////////////////////////////////////////////////////////////

using System;
using System.Collections;
using System.Text;
using System.Collections.Generic;


namespace Agnos
{
	/// <summary>
	/// an heterogeneous map. it is basically a regular Dictionary, but it 
	/// associates with each entry a packer for the key and a packer for the 
	/// value. for "simple types", for which a packer can be inferred, you may
	/// use the 2-argument version of Add() or the [] operator, but for all
	/// other types, you should use the 4-argument version of Add(), where you
	/// specify the packers for the key and value.
	///
	/// note: this class implements IDictionary, so it can be used by third-party
	/// code, but only for "simple types", for which a packer can be inferred
	/// </summary>
	public class HeteroMap : IDictionary
	{
		protected sealed class FieldInfo
		{
			public Packers.AbstractPacker keypacker;
			public Packers.AbstractPacker valpacker;
			public FieldInfo (Packers.AbstractPacker keypacker, Packers.AbstractPacker valpacker)
			{
				this.keypacker = keypacker;
				this.valpacker = valpacker;
			}
		}
		protected readonly Dictionary<object, FieldInfo> fields;
		protected readonly Hashtable data;

		public HeteroMap ()
		{
			fields = new Dictionary<object, FieldInfo> ();
			data = new Hashtable ();
		}
		public HeteroMap (int capacity)
		{
			fields = new Dictionary<object, FieldInfo> (capacity);
			data = new Hashtable (capacity);
		}
		public HeteroMap (HeteroMap other)
		{
			fields = new Dictionary<object, FieldInfo> (other.fields);
			data = new Hashtable (other.data);
		}

		public override string ToString ()
		{
			StringBuilder sb = new StringBuilder (5000);
			ToStringHelper ("", sb);
			return sb.ToString ();
		}

		protected void ToStringHelper (String indent, StringBuilder sb)
		{
			sb.Append (indent + "HeteroMap{\n");
			foreach (DictionaryEntry e in data) {
				sb.Append (indent + "    " + e.Key.ToString () + " = ");
				if (e.Value is HeteroMap) {
					((HeteroMap)(e.Value)).ToStringHelper (indent + "    ", sb);
				} else {
					sb.Append (e.Value.ToString());
				}
				sb.Append ("\n");
			}
			sb.Append (indent + "}");
		}

		public int Count {
			get { return data.Count; }
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
			get { return data.Values; }
		}

		public void Clear ()
		{
			data.Clear ();
			fields.Clear ();
		}
		public bool Contains (Object key)
		{
			return data.Contains (key);
		}
		public bool ContainsKey (Object key)
		{
			return data.ContainsKey (key);
		}
		public bool ContainsValue (Object value)
		{
			return data.ContainsValue (value);
		}
		public void CopyTo (Array array, int arrayIndex)
		{
			data.CopyTo (array, arrayIndex);
		}
		public void Update (HeteroMap other)
		{
			foreach (KeyValuePair<Object, FieldInfo> e in other.fields) {
				Add (e.Key, e.Value.keypacker, other.data[e.Key], e.Value.valpacker);
			}
		}
		IEnumerator IEnumerable.GetEnumerator ()
		{
			return (IEnumerator)GetEnumerator ();
		}
		public IDictionaryEnumerator GetEnumerator ()
		{
			return data.GetEnumerator ();
		}
		public void Remove (object key)
		{
			data.Remove (key);
			fields.Remove (key);
		}

		protected Packers.AbstractPacker getPackerForBuiltinType (object val)
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
			if (val == null) {
				return Packers.Null;
			}
			return null;
		}

		/// <summary>
		/// Adds the given given value (with the given value-packer) under the
		/// given key (with the given key packer) 
		/// </summary>
		/// <param name="key">
		/// The key (any object)
		/// </param>
		/// <param name="keypacker">
		/// The packer for the key (an AbstractPacker)
		/// </param>
		/// <param name="value">
		/// The value (any object)
		/// </param>
		/// <param name="valpacker">
		/// The packer for the value (an AbstractPacker)
		/// </param>
		public void Add (Object key, Packers.AbstractPacker keypacker, Object value, Packers.AbstractPacker valpacker)
		{
			//System.Console.Error.WriteLine("Add: {0}, {1}, {2}, {3}", key, keypacker, value, valpacker);
			if (keypacker == null || valpacker == null) {
				throw new ArgumentNullException ("keypacker and valpacker cannot be null");
			}
			FieldInfo fi = null;
			if (fields.TryGetValue (key, out fi)) {
				fi.keypacker = keypacker;
				fi.valpacker = valpacker;
			} else {
				fields.Add (key, new FieldInfo (keypacker, valpacker));
			}
			data.Add (key, value);
		}

		/// <summary>
		/// specialized version of Add
		/// </summary>
		public void Add (String key, String value)
		{
			Add (key, Packers.Str, value, Packers.Str);
		}
		/// <summary>
		/// specialized version of Add
		/// </summary>
		public void Add (String key, int value)
		{
			Add (key, Packers.Str, value, Packers.Int32);
		}
		/// <summary>
		/// specialized version of Add
		/// </summary>
		public void Add (int key, String value)
		{
			Add (key, Packers.Int32, value, Packers.Str);
		}
		/// <summary>
		/// specialized version of Add
		/// </summary>
		public void Add (int key, int value)
		{
			Add (key, Packers.Int32, value, Packers.Int32);
		}

		/// <summary>
		/// a Version of Add that implements IDictionary.Add. It attempts to 
		/// infer the packers for the key and for the value
		/// </summary>
		public void Add (Object key, Object value)
		{
			Packers.AbstractPacker keypacker = getPackerForBuiltinType (key);
			Packers.AbstractPacker valpacker = getPackerForBuiltinType (value);
			if (keypacker == null) {
				throw new ArgumentException ("cannot deduce key packer " + key.GetType ().ToString () + ", use 4-argument Add()");
			}
			if (valpacker == null) {
				throw new ArgumentException ("cannot deduce value packer " + value.GetType ().ToString () + ", use 4-argument Add()");
			}
			Add (key, keypacker, value, valpacker);
		}

		/// <summary>
		/// specialized version of Add that attempts to infer the packer for 
		/// the key, but the packer for the value must be provided
		/// </summary>
		public void Add (Object key, Object value, Packers.AbstractPacker valpacker)
		{
			Packers.AbstractPacker keypacker = getPackerForBuiltinType (key);
			if (keypacker == null) {
				keypacker = getKeyPacker (key);
			}
			if (keypacker == null) {
				throw new ArgumentException ("cannot deduce key packer, use 4-argument Add()");
			}
			Add (key, keypacker, value, valpacker);
		}

		/// <summary>
		/// Adds a new HeteroMap instance to this HeteroMap under the given key
		/// This is a convenience function, used by the Agnos binding code,
		/// but it's not expected to be useful to the general public.
		/// </summary>
		/// <param name="name">
		/// The key
		/// </param>
		/// <returns>
		/// a new HeteroMap instance
		/// </returns>
		public HeteroMap AddNewMap (String name)
		{
			HeteroMap hm = new HeteroMap ();
			Add (name, Packers.Str, hm, Packers.builtinHeteroMapPacker);
			return hm;
		}

		public bool TryGetValue (Object key, out Object value)
		{
			if (data.Contains (key)) {
				value = data[key];
				return true;
			} else {
				value = null;
				return false;
			}
		}

		public Object this[Object key] {
			get { return data[key]; }
			set { Add (key, value); }
		}

		/// <summary>
		/// returns the key-packer associated with the given vey
		/// </summary>
		public Packers.AbstractPacker getKeyPacker (Object key)
		{
			return fields[key].keypacker;
		}

		/// <summary>
		/// returns the value-packer associated with the given vey
		/// </summary>
		public Packers.AbstractPacker getValuePacker (Object key)
		{
			return fields[key].valpacker;
		}
	}
	
}
