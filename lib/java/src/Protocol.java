package agnos;

import java.io.*;
import java.util.*;
import java.lang.ref.*;

public class Protocol
{
	public static final byte CMD_PING				= 0;
	public static final byte CMD_INVOKE				= 1;
	public static final byte CMD_QUIT				= 2;
	public static final byte CMD_DECREF				= 3;
	public static final byte CMD_INCREF				= 4;
	public static final byte CMD_GETINFO				= 5;

	public static final byte REPLY_SUCCESS				= 0;
	public static final byte REPLY_PROTOCOL_ERROR		= 1;
	public static final byte REPLY_PACKED_EXCEPTION		= 2;
	public static final byte REPLY_GENERIC_EXCEPTION		= 3;

	public static final int INFO_META 		= 0;
	public static final int INFO_GENERAL 	= 1;
	public static final int INFO_FUNCTIONS 	= 2;

	public static final int	AGNOS_MAGIC				= 0x5af30cf7;
	
	public abstract static class PackedException extends Exception
	{
		public PackedException()
		{
		}
	}

	public static class ProtocolError extends Exception
	{
		public ProtocolError(String message)
		{
			super(message);
		}
	}

	public static class HandshakeError extends ProtocolError
	{
		public HandshakeError(String message)
		{
			super(message);
		}
	}

	public static class GenericException extends Exception
	{
		public String	message;
		public String	traceback;

		public GenericException(String message, String traceback)
		{
			this.message = message;
			this.traceback = traceback;
		}

		public String toString()
		{
			return "agnos.Protocol.GenericException: "
					+ message
					+ " with remote backtrace:\n"
					+ traceback
					+ "\t------------------- end of remote traceback -------------------";
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
	
	public static abstract class BaseProcessor implements Packers.ISerializer
	{
		protected Map<Long, Cell>	cells;
		protected ObjectIDGenerator	idGenerator;

		public BaseProcessor()
		{
			cells = new HashMap<Long, Cell>();
			idGenerator = new ObjectIDGenerator();
		}

		public Long store(Object obj)
		{
			if (obj == null) {
				return new Long(-1);
			}
			Long id = idGenerator.getID(obj);
			Cell cell = cells.get(id);
			if (cell == null) {
				cell = new Cell(obj);
				cells.put(id, cell);
			}
			// else {
			// cell.incref();
			// }
			return id;
		}

		public Object load(Long id)
		{
			if (id < 0) {
				return null;
			}
			Cell cell = cells.get(id);
			return cell.obj;
		}

		protected void incref(Long id)
		{
			Cell cell = cells.get(id);
			if (cell != null) {
				cell.incref();
			}
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

		protected void sendProtocolError(Transports.ITransport transport,
				ProtocolError exc) throws IOException
		{
			Packers.Int8.pack(REPLY_PROTOCOL_ERROR, transport);
			Packers.Str.pack(exc.toString(), transport);
		}

		protected void sendGenericException(Transports.ITransport transport,
				GenericException exc) throws IOException
		{
			Packers.Int8.pack(REPLY_GENERIC_EXCEPTION, transport);
			Packers.Str.pack(exc.message, transport);
			Packers.Str.pack(exc.traceback, transport);
		}

		protected void process(Transports.ITransport transport)
				throws Exception
		{
			int seq = transport.beginRead();
			int cmdid = (Byte) (Packers.Int8.unpack(transport));

			transport.beginWrite(seq);
			
			try {
				switch (cmdid) {
					case CMD_INVOKE:
						processInvoke(transport, seq);
						break;
					case CMD_DECREF:
						processDecref(transport, seq);
						break;
					case CMD_INCREF:
						processIncref(transport, seq);
						break;
					case CMD_GETINFO:
                        processGetInfo(transport, seq);
						break;
					case CMD_PING:
						processPing(transport, seq);
						break;
					case CMD_QUIT:
						processQuit(transport, seq);
						break;
					default:
						throw new ProtocolError("unknown command code: "
								+ cmdid);
				}
			} catch (ProtocolError exc) {
				transport.reset();
				sendProtocolError(transport, exc);
			} catch (GenericException exc) {
				transport.reset();
				sendGenericException(transport, exc);
			} catch (Exception ex) {
				transport.cancelWrite();
				throw ex;
			} finally {
				transport.endRead();
			}
			transport.endWrite();
		}

		protected void processDecref(Transports.ITransport transport,
				Integer seq) throws IOException
		{
			Long id = (Long) (Packers.Int64.unpack(transport));
			decref(id);
		}

		protected void processIncref(Transports.ITransport transport,
				Integer seq) throws IOException
		{
			Long id = (Long) (Packers.Int64.unpack(transport));
			incref(id);
		}

		protected void processQuit(Transports.ITransport transport, Integer seq)
				throws IOException
		{
		}

		protected void processPing(Transports.ITransport transport, Integer seq)
				throws IOException
		{
			String message = (String) (Packers.Str.unpack(transport));
			Packers.Int8.pack(REPLY_SUCCESS, transport);
			Packers.Str.pack(message, transport);
		}

        protected void processGetInfo(Transports.ITransport transport, int seq) 
        			throws IOException
        {
            int code = (Integer)(Packers.Int32.unpack(transport));
            HeteroMap map = new HeteroMap();
			
			switch (code)
			{
				case INFO_GENERAL:
					processGetGeneralInfo(map);
					break;
				case INFO_FUNCTIONS:
					processGetFunctionsInfo(map);
					break;
				case INFO_META:
				default:
					map.put("INFO_META", INFO_META);
					map.put("INFO_GENERAL", INFO_GENERAL);
					map.put("INFO_FUNCTIONS", INFO_FUNCTIONS);
					break;
			}
			
            Packers.Int8.pack(REPLY_SUCCESS, transport);
			Packers.builtinHeteroMapPacker.pack(info, transport);
        }
		
		protected abstract void processGetGeneralInfo(HeteroMap map);
		
		protected abstract void processGetFunctionsInfo(HeteroMap map);
		
		abstract protected void processInvoke(Transports.ITransport transport,
				int seq) throws Exception;
	}

	protected enum ReplySlotType
	{
		SLOT_EMPTY(false), 
		SLOT_DISCARDED(false), 
		SLOT_VALUE(true), 
		SLOT_GENERIC_EXCEPTION(true), 
		SLOT_PACKED_EXCEPTION(true);
		
		public boolean ready;
		
		private ReplySlotType(boolean ready) {
			this.ready = ready;
		}
	}

	protected static class ReplySlot
	{
		public ReplySlotType	type;
		public Object			value;

		public ReplySlot(Packers.AbstractPacker packer)
		{
			type = ReplySlotType.SLOT_EMPTY;
			value = packer;
		}
	}

	public static class BaseClientUtils
	{
		protected Map<Integer, Packers.AbstractPacker> packedExceptionsMap;
		protected int						seq;
		protected Map<Integer, ReplySlot>	replies;
		protected Map<Long, WeakReference>	proxies;
		public Transports.ITransport		transport;

		public BaseClientUtils(Transports.ITransport transport, 
					Map<Integer, Packers.AbstractPacker> packedExceptionsMap)
				throws Exception
		{
			this.transport = transport;
			this.packedExceptionsMap = packedExceptionsMap;
			seq = 0;
			replies = new HashMap<Integer, ReplySlot>(128);
			proxies = new HashMap<Long, WeakReference>();
		}

		public void close() throws IOException
		{
			if (transport != null) {
				transport.close();
				transport = null;
			}
		}

		protected synchronized int getSeq()
		{
			seq += 1;
			return seq;
		}

		public Object getProxy(Long objref)
		{
			WeakReference weak = proxies.get(objref);
			if (weak == null) {
				return null;
			}
			Object proxy = weak.get();
			if (proxy == null) {
				proxies.remove(objref);
				return null;
			}
			return proxy;
		}

		public void cacheProxy(Long objref, Object proxy)
		{
			proxies.put(objref, new WeakReference(proxy));
		}

		public void decref(Long id)
		{
			int seq = getSeq();
			try {
				Packers.Int8.pack(CMD_DECREF, transport);
				Packers.Int64.pack(id, transport);
			} catch (Exception ignored) {
				// ignored
			}
		}

		public int beginCall(int funcid, Packers.AbstractPacker packer)
				throws IOException
		{
			int seq = getSeq();
			transport.beginWrite(seq);
			Packers.Int8.pack(CMD_INVOKE, transport);
			Packers.Int32.pack(funcid, transport);
			replies.put(seq, new ReplySlot(packer));
			return seq;
		}

		public void endCall() throws IOException
		{
			transport.endWrite();
		}
		
		public void cancelCall() throws IOException
		{
			transport.cancelWrite();
		}

		public int tunnelRequest (byte[] blob) throws IOException
		{
			int seq = getSeq ();
			transport.beginWrite (seq);
			transport.write (blob, 0, blob.length);
			transport.endWrite ();
			replies.put(seq, new ReplySlot (Packers.MockupPacker));
			return seq;
		}

		public void decref (long id) throws Exception
		{
			int seq = getSeq ();
			transport.beginWrite (seq);
			try {
				Packers.Int8.pack (CMD_DECREF, transport);
				Packers.Int64.pack (id, transport);
				transport.endWrite ();
			} catch (Exception ex) {
				transport.cancelWrite ();
				throw ex;
			}
		}

		public int Ping (String payload, int msecs) throws IOException, ProtocolError, PackedException, GenericException
		{
			//DateTime t0 = DateTime.Now;
			int seq = getSeq ();
			transport.beginWrite (seq);
			Packers.Int8.pack (CMD_PING, transport);
			Packers.Str.pack (payload, transport);
			transport.endWrite ();
			replies.put(seq, new ReplySlot (Packers.Str));
			String reply;
			//try {
			reply = (String)getReply (seq, msecs);
			//} catch (TimeoutException ex) {
			//	DiscardReply (seq);
			//	throw ex;
			//}
			//TimeSpan dt = DateTime.Now - t0;
			if (reply != payload) {
				throw new ProtocolError ("reply does not match payload!");
			}
			//return dt.Milliseconds;
			return 0;
		}

		public Map getServiceInfo (int code) throws IOException, ProtocolError, PackedException, GenericException
		{
			int seq = getSeq ();
			transport.beginWrite (seq);
			Packers.Int8.pack (CMD_GETINFO, transport);
			Packers.Int32.pack (code, transport);
			transport.endWrite ();
			//replies.put(seq, new ReplySlot (_dict_of_strings));
			return (Map)getReply (seq);
		}
		
		protected PackedException loadPackedException() throws IOException, ProtocolError
		{
			Integer clsid = (Integer)Packers.Int32.unpack(transport);
			Packers.AbstractPacker packer = packedExceptionsMap.get(clsid);
			if (packer == null) {
				throw new ProtocolError("unknown exception class id: " + clsid);
			}
			return (PackedException)packer.unpack(transport);
		}
		
		protected ProtocolError loadProtocolError() throws IOException
		{
			String message = (String) Packers.Str.unpack(transport);
			return new ProtocolError(message);
		}

		protected GenericException loadGenericException() throws IOException
		{
			String message = (String) Packers.Str.unpack(transport);
			String traceback = (String) Packers.Str.unpack(transport);
			return new GenericException(message, traceback);
		}

		public void processIncoming(int timeout_msecs) throws IOException, ProtocolError
		{
			int seq = transport.beginRead();

			try {
				int code = (Byte) (Packers.Int8.unpack(transport));
				ReplySlot slot = replies.get(seq);
				
				if (slot == null || (slot.type != ReplySlotType.SLOT_EMPTY && 
						slot.type != ReplySlotType.SLOT_DISCARDED)) {
					throw new ProtocolError("invalid reply sequence: " + seq);
				}
				boolean discard = (slot.type == ReplySlotType.SLOT_DISCARDED);
				Packers.AbstractPacker packer = (Packers.AbstractPacker) slot.value;

				switch (code) {
				case REPLY_SUCCESS:
					if (packer == null) {
						slot.value = null;
					}
					else if (packer == Packers.MockupPacker) {
						slot.value = transport.readAll();
					}
					else {
						slot.value = packer.unpack(transport);
					}
					slot.type = ReplySlotType.SLOT_VALUE;
					break;
				case REPLY_PROTOCOL_ERROR:
					throw (ProtocolError) (loadProtocolError().fillInStackTrace());
				case REPLY_PACKED_EXCEPTION:
					slot.type = ReplySlotType.SLOT_PACKED_EXCEPTION;
					slot.value = loadPackedException();
					break;
				case REPLY_GENERIC_EXCEPTION:
					slot.type = ReplySlotType.SLOT_GENERIC_EXCEPTION;
					slot.value = loadGenericException();
					break;
				default:
					throw new ProtocolError("unknown reply code: " + code);
				}
				
				if (discard) {
					replies.remove(seq);
				}
			} finally {
				transport.endRead();
			}
		}

		public boolean isReplyReady(int seq)
		{
			ReplySlot slot = replies.get(seq);
			return slot.type.ready;
		}

		public void discardReply(int seq)
		{
			ReplySlot slot = replies.get(seq);
			if (slot == null) {
				return;
			}
			if (slot.type.ready) {
				replies.remove(seq);
			}
			else {
				slot.type = ReplySlotType.SLOT_DISCARDED;
			}
		}

		public ReplySlot waitReply(int seq, int msecs) 
				throws IOException, ProtocolError
		{
			while (!isReplyReady(seq)) {
				processIncoming(msecs);
			}
			return replies.remove(seq);
		}

		public Object getReply(int seq, int msecs) 
				throws IOException, PackedException, GenericException, ProtocolError
		{
			ReplySlot slot = waitReply(seq, msecs);
			if (slot.type == ReplySlotType.SLOT_VALUE) {
				return slot.value;
			}
			else if (slot.type == ReplySlotType.SLOT_PACKED_EXCEPTION) {
				((PackedException) slot.value).fillInStackTrace();
				throw (PackedException) slot.value;
			}
			else if (slot.type == ReplySlotType.SLOT_GENERIC_EXCEPTION) {
				((GenericException) slot.value).fillInStackTrace();
				throw (GenericException) slot.value;
			}
			else {
				throw new AssertionError("invalid slot type: " + slot.type);
			}
		}

		public Object getReply(int seq) 
				throws IOException, PackedException, GenericException, ProtocolError
		{
			return getReply(seq, -1);
		}
	}	
	
}
