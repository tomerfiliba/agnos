package agnos;

import java.io.*;
import java.util.*;

public class HeteroMap
{
	public static class FieldInfo
	{
		public Packers.AbstractPacker keypacker;
		public Packers.AbstractPacker valpacker;
		public HeteroValue(Packers.AbstractPacker keypacker, Packers.AbstractPacker valpacker)
		{
			this.keypacker = keypacker;
			this.valpacker = valpacker;
		}
	}
	
	protected Map<Object, HeteroValue> map;
	
	public HeteroMap()
	{
		map = new HashMap<Object, HeteroValue>();
		map = new HashMap();
	}
	public HeteroMap(int capacity)
	{
		map = new HashMap<Object, HeteroValue>(capacity);
	}
	public HeteroMap(HeteroMap other)
	{
		map = new HashMap<Object, HeteroValue>(other.fields);
	}
	
	public void putField(Object key, Packers.AbstractPacker keypacker, Packers.AbstractPacker valpacker)
	{
		fields.put(key, new )
	}
	
	public void put(Packers.AbstractPacker keypacker, Object key, Packers.AbstractPacker valpacker, Object value)
	{
		map.put(key, new HeteroValue(keypacker, valpacker, valpacker));
	}
	public void put(Byte key, Packers.AbstractPacker valpacker, Object value)
	{
		put(Int8, key, valpacker, value);
	}
	public void put(byte key, Packers.AbstractPacker valpacker, Object value)
	{
		put(Int8, new Byte(key), valpacker, value);
	}
	public void put(Short key, Packers.AbstractPacker valpacker, Object value)
	{
		put(Int16, key, valpacker, value);
	}
	public void put(short key, Packers.AbstractPacker valpacker, Object value)
	{
		put(Int16, new Short(key), valpacker, value);
	}
	public void put(Integer key, Packers.AbstractPacker valpacker, Object value)
	{
		put(Int32, key, valpacker, value);
	}
	public void put(int key, Packers.AbstractPacker valpacker, Object value)
	{
		put(Int32, new Integer(key), valpacker, value);
	}
	public void put(Long key, Packers.AbstractPacker valpacker, Object value)
	{
		put(Long, key, valpacker, value);
	}
	public void put(long key, Packers.AbstractPacker valpacker, Object value)
	{
		put(Int64, new Long(key), valpacker, value);
	}
	public void put(String key, Packers.AbstractPacker valpacker, Object value)
	{
		put(Str, key, valpacker, value);
	}
	
	public void update(Object key, Object value)
	{
		HeteroValue val = map.get(key);
		val.value = value;
	}
	
	public void putAll(HeteroMap other)
	{
		map.putAll(other.map);
	}
	
	public Object get(Object key)
	{
		HeteroValue hv = map.get(key);
		if (hv == null) {
			return null;
		}
		return hv.value;
	}
	
	void clear()
	{
		map.clear();
	}
	
	public boolean containsKey(Object key)
	{
		return map.containsKey(name);
	}
	
	public boolean containsValue(Object val)
	{
		return map.containsValue(val);
	}
	
	public Object remove(Object key)
	{
		return map.remove(key);
	}
	
	public int size()
	{
		return map.size();
	}
	
	public Collection<Object> keySet()
	{
		return map.keys();
	}
	public Collection<HeteroValue> values()
	{
		return map.values();
	}
	public Set<Map.Entry<Object, HeteroValue>> entrySet()
	{
		return map.entrySet();
	}
	
	public boolean equals(Object o)
	{
		if (o instanceof HeteroMap) {
			return map.equals(o.map);
		}
		else {
			return false;
		}
	}
	
	public int hashCode()
	{
		return map.hashCode();
	}

	//
	// specialized put -- integer key
	//
	public void put(Integer key, Byte value)
	{
		put(key, Int8, value);
	}
	public void put(Integer key, byte value)
	{
		put(key, Int8, new Byte(value));
	}
	public void put(Integer key, Boolean value)
	{
		put(key, Bool, value);
	}
	public void put(Integer key, boolean value)
	{
		put(key, Int8, new Boolean(value));
	}
	public void put(Integer key, Short value)
	{
		put(key, Int16, value);
	}
	public void put(Integer key, short value)
	{
		put(key, Int16, new Short(value));
	}
	public void put(Integer key, Integer value)
	{
		put(key, Int32, value);
	}
	public void put(Integer key, int value)
	{
		put(key, Int32, new Integer(value));
	}
	public void put(Integer key, Long value)
	{
		put(key, Int64, value);
	}
	public void put(Integer key, long value)
	{
		put(key, Int64, new Long(value));
	}
	public void put(Integer key, Double value)
	{
		put(key, Float, value);
	}
	public void put(Integer key, double value)
	{
		put(key, Float, new Double(value));
	}
	public void put(Integer key, String value)
	{
		put(key, Str, value);
	}
	public void put(Integer key, byte[] value)
	{
		put(key, Buffer, value);
	}
	public void put(Integer key, Date value)
	{
		put(key, Date, value);
	}

	//
	// specialized put -- string key
	//
	public void put(String key, Byte value)
	{
		put(key, Int8, value);
	}
	public void put(String key, byte value)
	{
		put(key, Int8, new Byte(value));
	}
	public void put(String key, Boolean value)
	{
		put(key, Bool, value);
	}
	public void put(String key, boolean value)
	{
		put(key, Int8, new Boolean(value));
	}
	public void put(String key, Short value)
	{
		put(key, Int16, value);
	}
	public void put(String key, short value)
	{
		put(key, Int16, new Short(value));
	}
	public void put(String key, Integer value)
	{
		put(key, Int32, value);
	}
	public void put(String key, int value)
	{
		put(key, Int32, new Integer(value));
	}
	public void put(String key, Long value)
	{
		put(key, Int64, value);
	}
	public void put(String key, long value)
	{
		put(key, Int64, new Long(value));
	}
	public void put(String key, Double value)
	{
		put(key, Float, value);
	}
	public void put(String key, double value)
	{
		put(key, Float, new Double(value));
	}
	public void put(String key, String value)
	{
		put(key, Str, value);
	}
	public void put(String key, byte[] value)
	{
		put(key, Buffer, value);
	}
	public void put(String key, Date value)
	{
		put(key, Date, value);
	}
}


