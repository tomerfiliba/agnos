import java.util.WeakHashMap;


public class ObjectIDGenerator
{
	protected WeakHashMap map;
	protected long counter;
	
	public ObjectIDGenerator()
	{
		map = new WeakHashMap();
		counter = 0;
	}
	
	public synchronized long getID(Object obj)
	{
		Object id = map.get(obj);
		if (id != null) {
			return (long)id;
		}
		else {
			counter += 1;
			map.put(obj, counter);
			return counter;
		}
	}
	
}

