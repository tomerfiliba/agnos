package agnos;

import java.io.*;
import java.util.*;

public class Protocol {
	public static final int CMD_PING = 0;
	public static final int CMD_INVOKE = 1;
	public static final int CMD_QUIT = 2;
	public static final int CMD_DECREF = 3;

	public static final int REPLY_SUCCESS = 0;
	public static final int REPLY_PROTOCOL_ERROR = 1;
	public static final int REPLY_PACKED_ERROR = 2;
	public static final int REPLY_GENERIC_ERROR = 3;

	public abstract static class PackedException extends Exception {
		public PackedException() {
		}

		public PackedException(String message) {
			super(message);
		}

		public abstract void pack(OutputStream stream) throws IOException;
	}

	public static class ProtocolError extends Exception {
		public ProtocolError(String message) {
			super(message);
		}
	}

	public static class GenericError extends Exception {
		public String traceback;
		
		public GenericError(String message, String traceback) {
			super(message);
			this.traceback = traceback;
		}
		
		public String toString()
		{
			return "agnos.Protocol.GenericError with remote backtrace:\n" + traceback + 
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

	public static abstract class BaseProcessor {
		protected Map<Long, Cell> cells;
		protected ObjectIDGenerator idGenerator;

		public BaseProcessor() {
			cells = new HashMap<Long, Cell>();
			idGenerator = new ObjectIDGenerator();
		}

		protected Long store(Object obj) {
			Long id = idGenerator.getID(obj);
			Cell cell = cells.get(id);
			if (cell == null) {
				cell = new Cell(obj);
				cells.put(id, cell);
			}
			else {
				cell.incref();
			}
			return id;
		}

		protected Object load(Long id) {
			Cell cell = cells.get(id);
			return cell.obj;
		}

		protected void decref(Long id) {
			Cell cell = cells.get(id);
			if (cell != null) {
				if (cell.decref()) {
					cells.remove(id);
				}
			}
		}

		protected void send_packed_exception(OutputStream outStream,
				Integer seq, PackedException exc) throws IOException {
			Packers.Int32.pack(new Integer(seq), outStream);
			Packers.Int8.pack(new Byte((byte) REPLY_PACKED_ERROR), outStream);
			exc.pack(outStream);
			outStream.flush();
		}

		protected void send_protocol_error(OutputStream outStream, Integer seq,
				ProtocolError exc) throws IOException {
			Packers.Int32.pack(new Integer(seq), outStream);
			Packers.Int8.pack(new Byte((byte) REPLY_PROTOCOL_ERROR), outStream);
			Packers.Str.pack(exc.toString(), outStream);
			outStream.flush();
		}

		protected String getExceptionTraceback(Exception exc)
		{
			StringWriter sw = new StringWriter();
	        PrintWriter pw = new PrintWriter(sw, true);
	        exc.printStackTrace(pw);
	        pw.flush();
	        sw.flush();
	        return sw.toString();
		}
		
		protected void send_generic_error(OutputStream outStream, Integer seq, Exception exc) throws IOException 
		{
			Packers.Int32.pack(new Integer(seq), outStream);
			Packers.Int8.pack(new Byte((byte) REPLY_GENERIC_ERROR), outStream);
			Packers.Str.pack(exc.toString(), outStream);
			Packers.Str.pack(getExceptionTraceback(exc), outStream);
			outStream.flush();
		}

		protected void process(InputStream inStream, OutputStream outStream)
				throws Exception, IOException {
			Integer seq = (Integer) (Packers.Int32.unpack(inStream));
			int cmdid = (Byte) (Packers.Int8.unpack(inStream));
			try {
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
			} catch (ProtocolError exc) {
				send_protocol_error(outStream, seq, exc);
			} catch (PackedException exc) {
				send_packed_exception(outStream, seq, exc);
			} catch (IOException exc) {
				throw exc;
			} catch (Exception exc) {
				send_generic_error(outStream, seq, exc);
			}
		}

		protected void process_decref(InputStream inStream,
				OutputStream outStream, Integer seq) throws IOException {
			Long id = (Long) (Packers.Int64.unpack(inStream));
			decref(id);
		}

		protected void process_quit(InputStream inStream,
				OutputStream outStream, Integer seq) throws IOException {
		}

		protected void process_ping(InputStream inStream,
				OutputStream outStream, Integer seq) throws IOException {
			String message = (String) (Packers.Str.unpack(inStream));
			Packers.Int32.pack(seq, outStream);
			Packers.Int8.pack(REPLY_SUCCESS, outStream);
			Packers.Str.pack(message, outStream);
			outStream.flush();
		}

		abstract protected void process_invoke(InputStream inStream,
				OutputStream outStream, int seq) throws Exception, IOException,
				PackedException, ProtocolError, GenericError;
	}

	public static abstract class BaseClient {
		protected InputStream _inStream;
		protected OutputStream _outStream;
		protected int _seq;

		public BaseClient(InputStream inStream, OutputStream outStream) {
			_inStream = inStream;
			_outStream = outStream;
			_seq = 0;
		}

		public BaseClient(Transports.ITransport transport) throws IOException {
			this(transport.getInputStream(), transport.getOutputStream());
		}

		public void close() throws IOException {
			if (_inStream != null) {
				_inStream.close();
				_outStream.close();
				_inStream = null;
				_outStream = null;
			}
		}

		protected synchronized int _get_seq() {
			_seq += 1;
			return _seq;
		}

		protected void _decref(Long id) {
			int seq = _get_seq();
			try {
				Packers.Int32.pack(new Integer(seq), _outStream);
				Packers.Int8.pack(new Integer(CMD_DECREF), _outStream);
				Packers.Int64.pack(id, _outStream);
			} catch (Exception ignored) {
				// ignored
			}
		}

		protected int _cmd_invoke(int funcid) throws IOException {
			int seq = _get_seq();
			Packers.Int32.pack(new Integer(seq), _outStream);
			Packers.Int8.pack(new Integer(CMD_INVOKE), _outStream);
			Packers.Int32.pack(new Integer(funcid), _outStream);
			return seq;
		}

		protected abstract PackedException _load_packed_exception()
				throws IOException, ProtocolError;

		protected ProtocolError _load_protocol_error() throws IOException {
			String message = (String) Packers.Str.unpack(_inStream);
			return new ProtocolError(message);
		}

		protected GenericError _load_generic_error() throws IOException {
			String message = (String) Packers.Str.unpack(_inStream);
			String traceback = (String) Packers.Str.unpack(_inStream);
			return new GenericError(message, traceback);
		}

		protected Object _read_reply(Packers.IPacker packer)
				throws IOException, ProtocolError, PackedException,
				GenericError {
			int seq = (Integer) (Packers.Int32.unpack(_inStream));
			int code = (Byte) (Packers.Int8.unpack(_inStream));
			
			switch (code) {
			case REPLY_SUCCESS:
				if (packer == null) {
					return null;
				}
				else {
					return packer.unpack(_inStream);
				}
			case REPLY_PROTOCOL_ERROR:
				throw (ProtocolError)(_load_protocol_error().fillInStackTrace());
			case REPLY_PACKED_ERROR:
				throw (PackedException)(_load_packed_exception().fillInStackTrace());
			case REPLY_GENERIC_ERROR:
				throw (GenericError)(_load_generic_error().fillInStackTrace());
			default:
				throw new ProtocolError("unknown reply code: " + code);
			}
		}
	}

}
