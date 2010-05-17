package agnos;

import java.io.*;
import java.util.*;
import java.lang.ref.*;


public class Protocol 
{
	public static final int CMD_PING = 0;
	public static final int CMD_INVOKE = 1;
	public static final int CMD_QUIT = 2;
	public static final int CMD_DECREF = 3;
	public static final int CMD_INCREF = 4;

	public static final int REPLY_SUCCESS = 0;
	public static final int REPLY_PROTOCOL_ERROR = 1;
	public static final int REPLY_PACKED_EXCEPTION = 2;
	public static final int REPLY_GENERIC_EXCEPTION = 3;

	public abstract static class PackedException extends Exception 
	{
		public PackedException() {
		}
	}

	public static class ProtocolError extends Exception 
	{
		public ProtocolError(String message) {
			super(message);
		}
	}

	public static class GenericException extends Exception 
	{
		public String message;
		public String traceback;
		
		public GenericException(String message, String traceback) {
			this.message = message;
			this.traceback = traceback;
		}
		
		public String toString()
		{
			return "agnos.Protocol.GenericException with remote backtrace:\n" + traceback + 
			"\t------------------- end of remote traceback -------------------"; 
		}
	}

	public static class ObjectIDGenerator {
		protected Map<Object, Long> map;
		protected Long counter;

		public ObjectIDGenerator() {
			map = new WeakHashMap<Object, Long>();
			counter = new Long(0);
		}

		public synchronized Long getID(Object obj) {
			Object id = map.get(obj);
			if (id != null) {
				return (Long) id;
			} else {
				counter += 1;
				map.put(obj, counter);
				return counter;
			}
		}
	}

	protected static class Cell {
		public int refcount;
		public Object obj;

		public Cell(Object obj) {
			refcount = 1;
			this.obj = obj;
		}

		public void incref() {
			refcount += 1;
		}

		public boolean decref() {
			refcount -= 1;
			return refcount <= 0;
		}
	}

	public static abstract class BaseProcessor implements Packers.ISerializer
	{
		protected Map<Long, Cell> cells;
		protected ObjectIDGenerator idGenerator;
		protected ByteArrayOutputStream sendBuffer;

		public BaseProcessor() {
			cells = new HashMap<Long, Cell>();
			idGenerator = new ObjectIDGenerator();
			sendBuffer = new ByteArrayOutputStream(128 * 1024);
		}

		public Long store(Object obj) {
			if (obj == null) {
				return new Long(-1);
			}
			Long id = idGenerator.getID(obj);
			Cell cell = cells.get(id);
			if (cell == null) {
				cell = new Cell(obj);
				cells.put(id, cell);
			}
			//else {
			//	cell.incref();
			//}
			return id;
		}

		public Object load(Long id) {
			if (id < 0) {
				return null;
			}
			Cell cell = cells.get(id);
			return cell.obj;
		}

		protected void incref(Long id) {
			Cell cell = cells.get(id);
			if (cell != null) {
				cell.incref();
			}
		}
		
		protected void decref(Long id) {
			Cell cell = cells.get(id);
			if (cell != null) {
				if (cell.decref()) {
					cells.remove(id);
				}
			}
		}

		protected static String getExceptionTraceback(Exception exc)
		{
			StringWriter sw = new StringWriter(2000);
	        PrintWriter pw = new PrintWriter(sw, true);
	        exc.printStackTrace(pw);
	        pw.flush();
	        sw.flush();
	        String[] lines = sw.toString().split("\r\n|\r|\n");
			StringWriter sw2 = new StringWriter(2000);
	        // drop first line, it's the message, not traceback
	        for (int i = 1; i < lines.length; i++) {
	        		sw2.write(lines[i]);
	        		sw2.write("\n");
	        }
	        return sw2.toString();
		}

		protected void send_protocol_error(OutputStream outStream, Integer seq, ProtocolError exc) throws IOException {
			Packers.Int32.pack(new Integer(seq), outStream);
			Packers.Int8.pack(new Byte((byte) REPLY_PROTOCOL_ERROR), outStream);
			Packers.Str.pack(exc.toString(), outStream);
		}

		protected void send_generic_exception(OutputStream outStream, Integer seq, GenericException exc) throws IOException 
		{
			Packers.Int32.pack(new Integer(seq), outStream);
			Packers.Int8.pack(new Byte((byte) REPLY_GENERIC_EXCEPTION), outStream);
			Packers.Str.pack(exc.message, outStream);
			Packers.Str.pack(exc.traceback, outStream);
		}

		protected void process(InputStream inStream, OutputStream outStream) throws Exception
		{
			Integer seq = (Integer) (Packers.Int32.unpack(inStream));
			int cmdid = (Byte) (Packers.Int8.unpack(inStream));

			sendBuffer.reset();
			try {
				switch (cmdid) {
				case CMD_INVOKE:
					process_invoke(inStream, sendBuffer, seq);
					break;
				case CMD_DECREF:
					process_decref(inStream, sendBuffer, seq);
					break;
				case CMD_INCREF:
					process_incref(inStream, sendBuffer, seq);
					break;
				case CMD_QUIT:
					process_quit(inStream, sendBuffer, seq);
					break;
				case CMD_PING:
					process_ping(inStream, sendBuffer, seq);
					break;
				default:
					throw new ProtocolError("unknown command code: " + cmdid);
				}
			} 
			catch (ProtocolError exc) {
				sendBuffer.reset();
				send_protocol_error(sendBuffer, seq, exc);
			} 
			catch (GenericException exc) {
				sendBuffer.reset();
				send_generic_exception(sendBuffer, seq, exc);
			}
			
			sendBuffer.writeTo(outStream);
			outStream.flush();
		}

		protected void process_decref(InputStream inStream, OutputStream outStream, Integer seq) throws IOException 
		{
			Long id = (Long) (Packers.Int64.unpack(inStream));
			decref(id);
		}

		protected void process_incref(InputStream inStream, OutputStream outStream, Integer seq) throws IOException 
		{
			Long id = (Long) (Packers.Int64.unpack(inStream));
			incref(id);
		}

		protected void process_quit(InputStream inStream, OutputStream outStream, Integer seq) throws IOException 
		{
		}

		protected void process_ping(InputStream inStream, OutputStream outStream, Integer seq) throws IOException 
		{
			String message = (String) (Packers.Str.unpack(inStream));
			Packers.Int32.pack(seq, outStream);
			Packers.Int8.pack(REPLY_SUCCESS, outStream);
			Packers.Str.pack(message, outStream);
		}

		abstract protected void process_invoke(InputStream inStream, OutputStream outStream, int seq) throws Exception;
	}

	protected enum ReplySlotType
	{
		SLOT_EMPTY,
		SLOT_DISCARDED,
		SLOT_VALUE,
		SLOT_EXCEPTION
	}
	
	protected static class ReplySlot
	{
		public ReplySlotType type;
		public Object value;
		
		public ReplySlot(Packers.IPacker packer)
		{
			type = ReplySlotType.SLOT_EMPTY;
			value = packer;
		}
	}
	
	public static abstract class BaseClient {
		protected InputStream _inStream;
		protected OutputStream _outStream;
		protected ByteArrayOutputStream _sendBuffer;
		protected int _seq;
		protected Map<Integer, ReplySlot> _replies;
		protected Map<Long, WeakReference> _proxies;

		public BaseClient(InputStream inStream, OutputStream outStream) 
		{
			_inStream = inStream;
			_outStream = outStream;
			_sendBuffer = new ByteArrayOutputStream(128 * 1024);
			_seq = 0;
			_replies = new HashMap<Integer, ReplySlot>(128);
			_proxies = new HashMap<Long, WeakReference>();
		}

		public void close() throws IOException 
		{
			if (_inStream != null) {
				_inStream.close();
				_outStream.close();
				_inStream = null;
				_outStream = null;
			}
		}

		protected synchronized int _get_seq() 
		{
			_seq += 1;
			return _seq;
		}
		
		protected Object _get_proxy(Long objref)
		{
			WeakReference weak = _proxies.get(objref);
			if (weak == null) {
				return null;
			}
			Object proxy = weak.get();
			if (proxy == null) {
				_proxies.remove(objref);
				return null;
			}
			return proxy;
		}

		protected void _decref(Long id) 
		{
			int seq = _get_seq();
			try {
				Packers.Int32.pack(new Integer(seq), _outStream);
				Packers.Int8.pack(new Integer(CMD_DECREF), _outStream);
				Packers.Int64.pack(id, _outStream);
				_outStream.flush();
			} catch (Exception ignored) {
				// ignored
			}
		}

		protected int _send_invocation(OutputStream stream, int funcid, Packers.IPacker packer) throws IOException 
		{
			int seq = _get_seq();
			Packers.Int32.pack(new Integer(seq), stream);
			Packers.Int8.pack(new Integer(CMD_INVOKE), stream);
			Packers.Int32.pack(new Integer(funcid), stream);
			_replies.put(seq, new ReplySlot(packer));
			return seq;
		}

		protected abstract PackedException _load_packed_exception() throws Exception;

		protected ProtocolError _load_protocol_error() throws IOException 
		{
			String message = (String) Packers.Str.unpack(_inStream);
			return new ProtocolError(message);
		}

		protected GenericException _load_generic_exception() throws IOException 
		{
			String message = (String) Packers.Str.unpack(_inStream);
			String traceback = (String) Packers.Str.unpack(_inStream);
			return new GenericException(message, traceback);
		}

		protected boolean _process_incoming(int timeout_msecs) throws Exception
		{
			int seq = (Integer) (Packers.Int32.unpack(_inStream));
			int code = (Byte) (Packers.Int8.unpack(_inStream));
			
			ReplySlot slot = _replies.get(seq);
			if (slot == null || (slot.type != ReplySlotType.SLOT_EMPTY && slot.type != ReplySlotType.SLOT_DISCARDED)) {
				throw new ProtocolError("invalid reply sequence: " + seq);
			}
			Packers.IPacker packer = (Packers.IPacker)slot.value;

			//System.out.println("C: got reply " + seq + " code = " + code);
			//System.out.println("C: packer = " + packer);

			switch (code) {
			case REPLY_SUCCESS:
				if (packer == null) {
					slot.value = null;
				}
				else {
					slot.value = packer.unpack(_inStream);
				}
				//System.out.println("C: slot.value = " + slot.value);
				slot.type = ReplySlotType.SLOT_VALUE;
				break;
			case REPLY_PROTOCOL_ERROR:
				throw (ProtocolError)(_load_protocol_error().fillInStackTrace());
			case REPLY_PACKED_EXCEPTION:
				slot.type = ReplySlotType.SLOT_EXCEPTION;
				slot.value = _load_packed_exception();
				break;
			case REPLY_GENERIC_EXCEPTION:
				slot.type = ReplySlotType.SLOT_EXCEPTION;
				slot.value = _load_generic_exception();
				break;
			default:
				throw new ProtocolError("unknown reply code: " + code);
			}
			
			return true;
		}
		
		protected boolean _is_reply_ready(int seq)
		{
			ReplySlot slot = _replies.get(seq);
			return slot.type == ReplySlotType.SLOT_VALUE || slot.type == ReplySlotType.SLOT_EXCEPTION;
		}
		
		protected ReplySlot _wait_reply(int seq, int timeout_msecs) throws Exception
		{
			while (!_is_reply_ready(seq)) {
				_process_incoming(timeout_msecs);
			}
			return _replies.remove(seq);
		}
		
		protected Object _get_reply(int seq, int timeout_msecs) throws Exception
		{
			ReplySlot slot = _wait_reply(seq, timeout_msecs);
			if (slot.type == ReplySlotType.SLOT_VALUE) {
				return slot.value;
			}
			else if (slot.type == ReplySlotType.SLOT_EXCEPTION) {
				((Exception)slot.value).fillInStackTrace();
				throw (Exception)slot.value;
			}
			else {
				throw new Exception("invalid slot type: " + slot.type);
			}
		}

		protected Object _get_reply(int seq) throws Exception
		{
			return _get_reply(seq, -1);
		}
	}

}














