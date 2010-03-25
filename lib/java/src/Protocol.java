package agnos;

import java.io.*;
import java.util.*;

public class Protocol
{
	public static final int CMD_PING = 0;
	public static final int CMD_INVOKE = 1;
	public static final int CMD_QUIT = 2;
	public static final int CMD_DECREF = 3;
	
	public static final int REPLY_SUCCESS = 0;
	public static final int REPLY_PROTOCOL_ERROR = 1;
	public static final int REPLY_GENERIC_ERROR = 2;
	public static final int REPLY_EXECUTION_ERROR = 3;

	
	public abstract static class PackedException extends Exception
	{
		public PackedException()
		{
		}
		public PackedException(String message)
		{
			super(message);
		}
        public abstract void pack(OutputStream stream) throws IOException;
	}

	/*public static class GenericException extends Exception
	{
		public String className;
		public GenericException(String className, String message)
		{
			super(message);
			this.className = className;
		}
	}*/
	
	public static class ProtocolError extends Exception
	{
		public ProtocolError(String message)
		{
			super(message);
		}
	}
	
	public static class ObjectIDGenerator
	{
		protected Map<Object, Long>	map;
		protected Long				counter;

		public ObjectIDGenerator()
		{
			map = new WeakHashMap<Object, Long>();
			counter = new Long(0);
		}

		public synchronized Long getID(Object obj)
		{
			Object id = map.get(obj);
			if (id != null) {
				return (Long) id;
			}
			else {
				counter += 1;
				map.put(obj, counter);
				return counter;
			}
		}
	}

	protected static class Cell
	{
		public int		refcount;
		public Object	obj;

		public Cell(Object obj)
		{
			refcount = 1;
			this.obj = obj;
		}

		public void incref()
		{
			refcount += 1;
		}

		public boolean decref()
		{
			refcount -= 1;
			return refcount <= 0;
		}
	}

	public static abstract class BaseProcessor
	{
		//protected InputStream		inStream;
		//protected OutputStream		outStream;
		protected Map<Long, Cell>	cells;
		protected ObjectIDGenerator	idGenerator;

		public BaseProcessor(/*InputStream inStream, OutputStream outStream*/)
        {
            //this.inStream = inStream;
            //this.outStream = outStream;
            cells = new HashMap<Long, Cell>();
            idGenerator = new ObjectIDGenerator();
        }

		protected Long store(Object obj)
		{
			Long id = idGenerator.getID(obj);
			Cell cell = cells.get(id);
			if (cell == null)
				cell = new Cell(obj);
			else
				cell.incref();
			return id;
		}

		protected Object load(Long id)
		{
			Cell cell = cells.get(id);
			return cell.obj;
		}

		protected void decref(Long id)
		{
			Cell cell = cells.get(id);
			if (cell != null) {
				if (cell.decref()) {
					cells.remove(id);
				}
			}
		}

		protected void send_packed_exception(OutputStream outStream, Integer seq, PackedException exc) throws IOException
		{
            Packers.Int32.pack(new Integer(seq), outStream);
            Packers.Int8.pack(new Byte((byte)Protocol.REPLY_EXECUTION_ERROR), outStream);
            exc.pack(outStream);
            outStream.flush();
		}

		protected void send_protocol_error(OutputStream outStream, Integer seq, ProtocolError exc) throws IOException
		{
            Packers.Int32.pack(new Integer(seq), outStream);
            Packers.Int8.pack(new Byte((byte)Protocol.REPLY_PROTOCOL_ERROR), outStream);
            Packers.Str.pack(exc.toString(), outStream);
            outStream.flush();
		}
		
		/*protected void send_generic_exception(OutputStream outStream, Integer seq, Exception exc) throws IOException
		{
            Packers.Int32.pack(new Integer(seq), outStream);
            Packers.Int8.pack(new Byte((byte)Protocol.REPLY_GENERIC_ERROR), outStream);
            Packers.Str.pack(exc.getClass().getName(), outStream);
            Packers.Str.pack(exc.toString(), outStream);
            outStream.flush();
		}*/

		protected void process(InputStream inStream, OutputStream outStream) throws IOException
		{
			Integer seq = (Integer) (Packers.Int32.unpack(inStream));
			int cmdid = (Byte) (Packers.Int8.unpack(inStream));
			try 
			{
				switch (cmdid) {
					case CMD_INVOKE:
						process_invoke(inStream, outStream, seq);
						break;
					case CMD_DECREF:
						process_decref(inStream, outStream, seq);
						break;
					case CMD_QUIT:
						process_quit(inStream, outStream, seq);
						break;
					case CMD_PING:
						process_ping(inStream, outStream, seq);
						break;
					default:
						throw new ProtocolError("unknown command code: " + cmdid);
				}
			}
			catch (ProtocolError exc)
			{
				send_protocol_error(outStream, seq, exc);
			}
			catch (PackedException exc)
			{
				send_packed_exception(outStream, seq, exc);
			}
		}

		protected void process_decref(InputStream inStream, OutputStream outStream, Integer seq) throws IOException
		{
			Long id = (Long) (Packers.Int64.unpack(inStream));
			decref(id);
		}

		protected void process_quit(InputStream inStream, OutputStream outStream, Integer seq) throws IOException
		{
		}

		protected void process_ping(InputStream inStream, OutputStream outStream, Integer seq) throws IOException
		{
			String message = (String)(Packers.Str.unpack(inStream));
			Packers.Int32.pack(seq, outStream);
			Packers.Int8.pack(REPLY_SUCCESS, outStream);
			Packers.Str.pack(message, outStream);
			outStream.flush();
		}

		abstract protected void process_invoke(InputStream inStream, OutputStream outStream, int seq) throws IOException, PackedException, ProtocolError;
	}
	
	public static abstract class BaseClient
	{
        protected InputStream _inStream;
        protected OutputStream _outStream;
        protected int _seq;
        
        public BaseClient(InputStream inStream, OutputStream outStream)
        {
            _inStream = inStream;
            _outStream = outStream;
            _seq = 0;
        }
        
        protected synchronized int _get_seq()
        {
            _seq += 1;
        	return _seq;
        }
        
        protected void _decref(Long id)
        {
        	int seq = _get_seq();
        	try
        	{
	            Packers.Int32.pack(new Integer(seq), _outStream);
	            Packers.Int8.pack(new Integer(CMD_DECREF), _outStream);
	            Packers.Int64.pack(id, _outStream);
        	}
        	catch (Exception ignored) {
        		// ignored
        	}
        }

        protected int _cmd_invoke(int funcid) throws IOException
        {
        	int seq = _get_seq();
            Packers.Int32.pack(new Integer(seq), _outStream);
            Packers.Int8.pack(new Integer(CMD_INVOKE), _outStream);
            Packers.Int32.pack(new Integer(funcid), _outStream);
            return seq;
        }

        protected abstract PackedException _load_packed_exception() throws IOException, ProtocolError;

        /*protected GenericException _load_generic_exception() throws IOException
        {
        	String className = (String)Packers.Str.unpack(_inStream);
        	String message = (String)Packers.Str.unpack(_inStream);
        	return new GenericException(className, message);
        }*/

        protected ProtocolError _load_protocol_error() throws IOException
        {
        	String message = (String)Packers.Str.unpack(_inStream);
        	return new ProtocolError(message);
        }

        protected Object _read_reply(Packers.IPacker packer) throws IOException, ProtocolError, PackedException
        {
            int code = (Byte)(Packers.Int8.unpack(_inStream));
            switch (code)
            {
            	case REPLY_SUCCESS:
            		return packer.unpack(_inStream);
            	case REPLY_PROTOCOL_ERROR:
            		throw _load_protocol_error();
            	//case REPLY_GENERIC_ERROR:
            	//	throw _load_generic_exception();
            	case REPLY_EXECUTION_ERROR:
            		throw _load_packed_exception();
            	default:
            		throw new Protocol.ProtocolError("unknown reply code: " + code);
            }
        }	
	}
	
	
}
