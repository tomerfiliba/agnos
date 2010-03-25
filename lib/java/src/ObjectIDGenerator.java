package agnos;

import java.util.*;

public class ObjectIDGenerator
{
	protected Map<Object, Long> map;
	protected Long counter;
	
	public ObjectIDGenerator()
	{
		map = new WeakHashMap<Object, Long>();
		counter = new Long(0);
	}
	
	public synchronized Long getID(Object obj)
	{
		Object id = map.get(obj);
		if (id != null) {
			return (Long)id;
		}
		else {
			counter += 1;
			map.put(obj, counter);
			return counter;
		}
	}
}

