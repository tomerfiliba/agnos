package agnos;

import java.io.*;
import java.util.*;

public class HeteroMap
{
	public static class FieldInfo
	{
		public Packers.AbstractPacker keypacker;
		public Packers.AbstractPacker valpacker;
		public FieldInfo(Packers.AbstractPacker keypacker, Packers.AbstractPacker valpacker)
		{
			this.keypacker = keypacker;
			this.valpacker = valpacker;
		}
	}
	
	protected Map<Object, FieldInfo> fields;
	protected Map<Object, Object> data;
	
	public HeteroMap()
	{
		fields = new HashMap<Object, FieldInfo>();
		data = new HashMap<Object, Object>();
	}
	public HeteroMap(int capacity)
	{
		fields = new HashMap<Object, FieldInfo>(capacity);
		data = new HashMap<Object, Object>(capacity);
	}
	public HeteroMap(HeteroMap other)
	{
		fields = new HashMap<Object, FieldInfo>(other.fields);
		data = new HashMap<Object, Object>(other.data);
	}

	void clear()
	{
		fields.clear();
		data.clear();
	}
	public boolean containsKey(Object key)
	{
		return data.containsKey(name);
	}
	public boolean containsValue(Object val)
	{
		return data.containsValue(val);
	}
	public int size()
	{
		return data.size();
	}
	public Collection keySet()
	{
		return data.keys();
	}
	public Collection values()
	{
		return data.values();
	}
	public Set<Map.Entry> entrySet()
	{
		return map.entrySet();
	}
	
	public boolean equals(Object o)
	{
		if (o instanceof HeteroMap) {
			return fields.equals(o.fields) && data.equals(o.data);
		}
		else {
			return false;
		}
	}
	public int hashCode()
	{
		return fields.hashCode();
	}	
	
	public void put(Object key, Packers.AbstractPacker keypacker, Object value, Packers.AbstractPacker valpacker)
	{
		fields.put(key, new FieldInfo(keypacker, valpacker));
		data.put(key, value);
	}
	public void putAll(HeteroMap other)
	{
		fields.putAll(other.fields);
		data.putAll(data.fields);
	}
	
	public void put(Integer key, Object value, Packers.AbstractPacker valpacker)
	{
		put(key, Packers.Int32, value, valpacker);
	}
	public void put(Integer key, Integer value)
	{
		put(key, Packers.Int32, value, Packers.Int32);
	}
	public void put(Integer key, String value)
	{
		put(key, Packers.Int32, value, Packers.Str);
	}
	
	public void put(String key, Object value, Packers.AbstractPacker valpacker)
	{
		put(key, Packers.Str, value, valpacker);
	}
	public void put(String key, Integer value)
	{
		put(key, Packers.Str, value, Packers.Int32);
	}
	public void put(String key, String value)
	{
		put(key, Packers.Str, value, Packers.Str);
	}
	
	public void remove(Object key)
	{
		fields.remove(key);
		data.remove(key);
	}
	
	public void set(Object key, Object value)
	{
		if (!fields.containsKey(key)) {
			throw new HeteroMapException("field was not set");
		}
		data.put(key, value);
	}
	
	public Object get(Object key)
	{
		return data.get(key);
	}

	protected FieldInfo getFieldInfo(Object key)
	{
		return fields.get(key);
	}
	

}


