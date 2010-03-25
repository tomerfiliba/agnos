package agnos;

import java.utils.*;

public class Protocol
{
	public enum CommandCodes
	{
		CMD_INVOKE, CMD_QUIT, CMD_DECREF, CMD_PING
	}

	public enum ReplyCodes
	{
		REPLY_SUCCESS, REPLY_PROTOCOL_ERROR, REPLY_EXECUTION_ERROR,
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

	public static class BaseProcessor
	{
		protected InputStream		inStream;
		protected OutputStream		outStream;
		protected Map<Long, Cell>	cells;
		protected ObjectIDGenerator	idGenerator;

		public BaseProcessor(InputStream inStream, OutputStream outStream)
        {
            this.inStream = inStream;
            this.outStream = outStream;
            cells = new HashMap<Long, Cell>;
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

		protected void process()
		{
			int seq = (Integer) (Packers.Int32.unpack(inStream));
			int cmdid = (Byte) (Packers.Int8.unpack(inStream));
			switch (cmdid) {
				case CMD_INVOKE:
					process_invoke(seq);
					break;
				case CMD_DECREF:
					process_decref(seq);
					break;
				case CMD_QUIT:
					process_quit(seq);
					break;
				case CMD_PING:
					process_ping(seq);
					break;
				default:
					// unknown command
					break;
			}
		}

		protected void process_decref(int seq)
		{
			Long id = (Long) (Packers.Int64.unpack(inStream));
			decref(id);
		}

		protected void process_quit(int seq)
		{
		}

		protected void process_ping(int seq)
		{
		}

		abstract protected void process_invoke(int seq);
	}
	
	public static class BaseClient
	{
        protected InputStream _inStream;
        protected OutputStream _outStream;
        protected int _seq;
        
        public BaseClient(InputStream inStream, OutputStream, outStream)
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

        public int _cmd_invoke(int funcid)
        {
        	int seq = _get_seq();
            Packers.Int32.pack(new Integer(seq), _outStream);
            Packers.Int8.pack(new Integer(CMD_INVOKE), _outStream);
            Packers.Int32.pack(new Integer(funcid), _outStream);
        }
        
        public Object _read_result(IPacker packer)
        {
            ResultCodes code = (ResultCodes)(Packers.Int8.pack(_inStream));
            if (code == RESULT_SUCCESS)
            {
                return packer.unpack(_inStream);
            }
            else
            {
                throw new Exception("oops");
            }
        }		
	}
	
	
}
