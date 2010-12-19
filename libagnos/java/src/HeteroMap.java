//////////////////////////////////////////////////////////////////////////////
// Part of the Agnos RPC Framework
//    http://agnos.sourceforge.net
//
// Copyright 2010, International Business Machines Corp.
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

package agnos;

import java.io.*;
import java.util.*;


public class HeteroMap implements Map
{
	protected static final class FieldInfo
	{
		public Packers.AbstractPacker keypacker;
		public Packers.AbstractPacker valpacker;
		public FieldInfo(Packers.AbstractPacker keypacker, Packers.AbstractPacker valpacker)
		{
			this.keypacker = keypacker;
			this.valpacker = valpacker;
		}
	}
	
	protected final Map<Object, FieldInfo> fields;
	protected final Map data;
	
	public HeteroMap()
	{
		fields = new HashMap<Object, FieldInfo>();
		data = new HashMap();
	}
	public HeteroMap(int capacity)
	{
		fields = new HashMap<Object, FieldInfo>(capacity);
		data = new HashMap(capacity);
	}
	public HeteroMap(HeteroMap other)
	{
		fields = new HashMap<Object, FieldInfo>(other.fields);
		data = new HashMap(other.data);
	}
	
	public HeteroMap add(Object key, Object value)
	{
		put(key, value);
		return this;
	}
	
	public String toString()
	{
		StringWriter sw = new StringWriter(2000);
		sw.write("HeteroMap{\n");
		for (Map.Entry e : (Set<Map.Entry>)data.entrySet()) {
			sw.write("    " + e.getKey().toString() + " : " + e.getValue().toString() + "\n");
		}
		sw.write("}");
		sw.flush();
		return sw.toString();
	}

	public void clear()
	{
		fields.clear();
		data.clear();
	}
	public boolean containsKey(Object key)
	{
		return data.containsKey(key);
	}
	public boolean containsValue(Object val)
	{
		return data.containsValue(val);
	}
	public int size()
	{
		return data.size();
	}
	public Set keySet()
	{
		return data.keySet();
	}
	public Collection values()
	{
		return data.values();
	}
	public Set<Map.Entry> entrySet()
	{
		return data.entrySet();
	}
	
	public boolean equals(Object o)
	{
		if (o instanceof HeteroMap) {
			HeteroMap hm = (HeteroMap)o;
			return fields.equals(hm.fields) && data.equals(hm.data);
		}
		else {
			return false;
		}
	}
	public int hashCode()
	{
		return fields.hashCode();
	}	
	
	public HeteroMap putNewMap(String name)
	{
		HeteroMap hm = new HeteroMap();
		put(name, Packers.Str, hm, Packers.builtinHeteroMapPacker);
		return hm;
	}
	
	public Object put(Object key, Packers.AbstractPacker keypacker, Object value, Packers.AbstractPacker valpacker)
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
	
	protected Packers.AbstractPacker getPackerForBuiltinType(Object val)
	{
		if (val instanceof String) {
			return Packers.Str;
		}
		if (val instanceof Integer) {
			return Packers.Int32;
		}
		if (val instanceof Long) {
			return Packers.Int64;
		}
		if (val instanceof Double || val instanceof Float) {
			return Packers.Float;
		}
		if (val instanceof Byte) {
			return Packers.Int8;
		}
		if (val instanceof Short) {
			return Packers.Int16;
		}
		if (val instanceof Date) {
			return Packers.Date;
		}
		if (val instanceof byte[]) {
			return Packers.Buffer;
		}
		if (val == null) {
			return Packers.Null;
		}
		return null;
	}
	
	public Object put(Object key, Object value)
	{
		Packers.AbstractPacker keypacker = getPackerForBuiltinType(key);
		Packers.AbstractPacker valpacker = getPackerForBuiltinType(value);
		
		if (keypacker == null || valpacker == null) {
			throw new IllegalArgumentException("cannot deduce key or value packer, use the 4-argument put()");
		}
		
		return put(key, keypacker, value, valpacker);
	}

	public Object put(Object key, Object value, Packers.AbstractPacker valpacker)
	{
		Packers.AbstractPacker keypacker = getPackerForBuiltinType(key);
		if (keypacker == null) {
			keypacker = getKeyPacker(key);
			if (keypacker == null) {
				throw new IllegalArgumentException("cannot deduce key packer, use the 4-argument put()");
			}
		}
		
		return put(key, keypacker, value, valpacker);
	}

	public Object put(Integer key, String value)
	{
		return put(key, Packers.Int32, value, Packers.Str);
	}
	public Object put(Integer key, Integer value)
	{
		return put(key, Packers.Int32, value, Packers.Int32);
	}
	public Object put(String key, String value)
	{
		return put(key, Packers.Str, value, Packers.Str);
	}
	public Object put(String key, Integer value)
	{
		return put(key, Packers.Str, value, Packers.Int32);
	}
	
	public void putAll(Map other)
	{
		if (other instanceof HeteroMap) {
			HeteroMap hm = (HeteroMap)other;
			fields.putAll(hm.fields);
			data.putAll(hm.data);
		}
		else {
			for (Map.Entry e : (Set<Map.Entry>)other.entrySet()) {
				put(e.getKey(), e.getValue());
			}
		}
	}
	
	public Object remove(Object key)
	{
		fields.remove(key);
		return data.remove(key);
	}
	
	public boolean isEmpty()
	{
		return data.isEmpty();
	}
	
	public Object get(Object key)
	{
		return data.get(key);
	}

	protected Packers.AbstractPacker getKeyPacker(Object key)
	{
		FieldInfo fi = fields.get(key);
		if (fi == null) {
			return null;
		}
		return fi.keypacker;
	}

	protected Packers.AbstractPacker getValuePacker(Object key)
	{
		FieldInfo fi = fields.get(key);
		if (fi == null) {
			return null;
		}
		return fi.valpacker;
	}
}


