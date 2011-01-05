// ////////////////////////////////////////////////////////////////////////////
// Part of the Agnos RPC Framework
// http://agnos.sourceforge.net
//
// Copyright 2011, International Business Machines Corp.
// Author: Tomer Filiba (tomerf@il.ibm.com)
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
// http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.
// ////////////////////////////////////////////////////////////////////////////

package agnos.util;

import java.io.StringWriter;
import java.util.Collection;
import java.util.Date;
import java.util.HashMap;
import java.util.Map;
import java.util.Set;

import agnos.packers.AbstractPacker;
import agnos.packers.Builtin;


/**
 * HeteroMap, or "heterogeneous map", is a form of Map where there are no
 * restrictions imposed on the types of keys and values. It works by associating
 * each key-value pair with a key-packer and value-packer pair, that are used
 * to pack them. This way it can be serialized safely.
 * 
 * @author Tomer Filiba
 */
public class HeteroMap implements Map<Object, Object>
{
	protected static final class FieldInfo
	{
		public AbstractPacker keypacker;
		public AbstractPacker valpacker;

		public FieldInfo(AbstractPacker keypacker, AbstractPacker valpacker)
		{
			this.keypacker = keypacker;
			this.valpacker = valpacker;
		}
	}

	protected final Map<Object, FieldInfo> fields;
	protected final Map<Object, Object> data;

	/**
	 * Constructs an empty HeteroMap
	 */
	public HeteroMap()
	{
		fields = new HashMap<Object, FieldInfo>();
		data = new HashMap<Object, Object>();
	}

	/**
	 * Constructs an empty HeteroMap with the given initial capacity
	 */
	public HeteroMap(int capacity)
	{
		fields = new HashMap<Object, FieldInfo>(capacity);
		data = new HashMap<Object, Object>(capacity);
	}

	/**
	 * Constructs a HeteroMap by copying the given HeteroMap instance (shallow
	 * copy)
	 */
	public HeteroMap(HeteroMap other)
	{
		fields = new HashMap<Object, FieldInfo>(other.fields);
		data = new HashMap<Object, Object>(other.data);
	}

	@Override
	public String toString()
	{
		StringWriter sw = new StringWriter(2000);
		toString("", sw);
		sw.flush();
		return sw.toString();
	}

	protected void toString(String indent, StringWriter sw)
	{
		sw.write(indent + "HeteroMap {\n");
		for (Map.Entry<Object, Object> e : (Set<Map.Entry<Object, Object>>) data
				.entrySet()) {
			sw.write(indent + "    " + e.getKey().toString() + " : ");
			if (e.getValue() instanceof HeteroMap) {
				((HeteroMap) (e.getValue())).toString(indent + "    ", sw);
			}
			else {
				sw.write(e.getValue().toString());
			}
			sw.write("\n");
		}
		sw.write(indent + "}");
	}

	@Override
	public void clear()
	{
		fields.clear();
		data.clear();
	}

	@Override
	public boolean containsKey(Object key)
	{
		return data.containsKey(key);
	}

	@Override
	public boolean containsValue(Object val)
	{
		return data.containsValue(val);
	}

	@Override
	public int size()
	{
		return data.size();
	}

	@Override
	public Set<Object> keySet()
	{
		return data.keySet();
	}

	@Override
	public Collection<Object> values()
	{
		return data.values();
	}

	@Override
	public Set<Map.Entry<Object, Object>> entrySet()
	{
		return data.entrySet();
	}

	@Override
	public boolean equals(Object o)
	{
		if (o instanceof HeteroMap) {
			HeteroMap hm = (HeteroMap) o;
			return fields.equals(hm.fields) && data.equals(hm.data);
		}
		else {
			return false;
		}
	}

	@Override
	public int hashCode()
	{
		return fields.hashCode();
	}

	/**
	 * Convenience method that inserts a new HeteroMap instance into the
	 * HeteroMap, with the given name
	 * 
	 * @param name
	 *            the name of the HeteroMap to create
	 * @return the newly created HeteroMap
	 */
	public HeteroMap putNewMap(String name)
	{
		HeteroMap hm = new HeteroMap();
		put(name, Builtin.Str, hm, Builtin.heteroMapPacker);
		return hm;
	}

	/**
	 * A convenience methods that allows you to easily construct HeteroMap
	 * instances. For example:
	 * 
	 * new HeteroMap().add("a", "b").add(5, "foo").add("spam", "eggs")
	 * 
	 * @param key
	 *            the key
	 * @param value
	 *            the value
	 * 
	 * @return this (useful for concatenation)
	 */
	public HeteroMap add(Object key, Object value)
	{
		put(key, value);
		return this;
	}

	/**
	 * A convenience methods that allows you to easily construct HeteroMap
	 * instances. This is the four-argument form of add().
	 * 
	 * @see #add(Object, Object)
	 * 
	 * @param key
	 *            the key
	 * @param keypacker
	 *            the key packer
	 * @param value
	 *            the value
	 * @param valpacker
	 *            the value packer
	 * 
	 * @return this (useful for concatenation)
	 */
	public HeteroMap add(Object key, AbstractPacker keypacker, Object value,
			AbstractPacker valpacker)
	{
		put(key, keypacker, value, valpacker);
		return this;
	}

	/**
	 * Four-argument version of put. Puts the given key-value pair in this map,
	 * along with custom key and value packers.
	 * 
	 * @param key
	 *            the key
	 * @param keypacker
	 *            the key packer
	 * @param value
	 *            the value
	 * @param valpacker
	 *            the value packer
	 * 
	 * @return the previous value associated with key, or null if there was no
	 *          mapping for key
	 */
	public Object put(Object key, AbstractPacker keypacker, Object value,
			AbstractPacker valpacker)
	{
		FieldInfo fi = fields.get(key);
		if (fi == null) {
			fields.put(key, new FieldInfo(keypacker, valpacker));
		}
		else {
			fi.keypacker = keypacker;
			fi.valpacker = valpacker;
		}
		return data.put(key, value);
	}

	protected AbstractPacker getPackerForBuiltinType(Object val)
	{
		if (val instanceof String) {
			return Builtin.Str;
		}
		if (val instanceof Integer) {
			return Builtin.Int32;
		}
		if (val instanceof Long) {
			return Builtin.Int64;
		}
		if (val instanceof Double || val instanceof Float) {
			return Builtin.Float;
		}
		if (val instanceof Byte) {
			return Builtin.Int8;
		}
		if (val instanceof Short) {
			return Builtin.Int16;
		}
		if (val instanceof Date) {
			return Builtin.Date;
		}
		if (val instanceof byte[]) {
			return Builtin.Buffer;
		}
		if (val == null) {
			return Builtin.Null;
		}
		return null;
	}

	/**
	 * Two-argument version of put (required by the interface). Puts the given
	 * key-value pair in this map, with the key and value packers being deduced.
	 * If they cannot be deduced, an IllegalArgumentException is thrown.
	 * 
	 * @param key
	 *            the key
	 * @param value
	 *            the value
	 * 
	 * @return the previous value associated with key, or null if there was no
	 *          mapping for key
	 */
	@Override
	public Object put(Object key, Object value)
	{
		AbstractPacker keypacker = getPackerForBuiltinType(key);
		AbstractPacker valpacker = getPackerForBuiltinType(value);

		if (keypacker == null || valpacker == null) {
			throw new IllegalArgumentException(
					"cannot deduce key or value packer, use the 4-argument put()");
		}

		return put(key, keypacker, value, valpacker);
	}

	/**
	 * Three-argument version of put. Puts the given key-value pair in this map,
	 * along with a custom value packer. The key packer is deduced. If it
	 * cannot be deduced, an IllegalArgumentException is thrown.
	 * 
	 * @param key
	 *            the key
	 * @param value
	 *            the value
	 * @param valpacker
	 *            the value packer
	 * 
	 * @return the previous value associated with key, or null if there was no
	 *          mapping for key
	 */
	public Object put(Object key, Object value, AbstractPacker valpacker)
	{
		AbstractPacker keypacker = getPackerForBuiltinType(key);
		if (keypacker == null) {
			keypacker = getKeyPacker(key);
			if (keypacker == null) {
				throw new IllegalArgumentException(
						"cannot deduce key packer, use the 4-argument put()");
			}
		}

		return put(key, keypacker, value, valpacker);
	}

	/**
	 * Specialized version of put
	 */
	public Object put(Integer key, String value)
	{
		return put(key, Builtin.Int32, value, Builtin.Str);
	}

	/**
	 * Specialized version of put
	 */
	public Object put(Integer key, Integer value)
	{
		return put(key, Builtin.Int32, value, Builtin.Int32);
	}

	/**
	 * Specialized version of put
	 */
	public Object put(String key, String value)
	{
		return put(key, Builtin.Str, value, Builtin.Str);
	}

	/**
	 * Specialized version of put
	 */
	public Object put(String key, Integer value)
	{
		return put(key, Builtin.Str, value, Builtin.Int32);
	}

	/**
	 * Copies all the elements of 'other' into this instance
	 * 
	 * @param other
	 *            the map to copy
	 */
	@Override
	public void putAll(Map other)
	{
		if (other instanceof HeteroMap) {
			HeteroMap hm = (HeteroMap) other;
			fields.putAll(hm.fields);
			data.putAll(hm.data);
		}
		else {
			for (Map.Entry<Object, Object> e : (Set<Map.Entry<Object, Object>>) other
					.entrySet()) {
				put(e.getKey(), e.getValue());
			}
		}
	}

	@Override
	public Object remove(Object key)
	{
		fields.remove(key);
		return data.remove(key);
	}

	@Override
	public boolean isEmpty()
	{
		return data.isEmpty();
	}

	@Override
	public Object get(Object key)
	{
		return data.get(key);
	}

	protected AbstractPacker getKeyPacker(Object key)
	{
		FieldInfo fi = fields.get(key);
		if (fi == null) {
			return null;
		}
		return fi.keypacker;
	}

	protected AbstractPacker getValuePacker(Object key)
	{
		FieldInfo fi = fields.get(key);
		if (fi == null) {
			return null;
		}
		return fi.valpacker;
	}
}
