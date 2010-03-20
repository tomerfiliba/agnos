package agnostic.datatypes;

import java.io.*;


public class Datatypes
{
	public static class Datatype
	{
		public abstract void pack(Object obj, OutputStream stream);
		public abstract Object unpack(InputStream stream);
	}
	
	public static class Int8_ extends Datatype
	{
		public void pack(Object obj, OutputStream stream)
		{
			stream.write((Integer)obj);
		}
		public Object unpack(InputStream stream)
		{
			return stream.read(1);
		}
	}
	
	static Int8_ Int8;
}
