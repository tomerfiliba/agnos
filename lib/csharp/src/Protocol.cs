using System;
using System.Collections;
using System.Collections.Generic;
using System.Text;
using System.Net;
using System.IO;
using System.Runtime.Serialization;
using Agnos.Transports;


namespace Agnos
{
	public abstract class PackedException : Exception
	{
		public PackedException ()
		{
		}
	}

	public class ProtocolError : Exception
	{
		public ProtocolError (String message) : base(message)
		{
		}
	}

	public class HandshakeError : ProtocolError
	{
		public HandshakeError (String message) : base(message)
		{
		}
	}


	public class GenericException : Exception
	{
		public String Traceback;

		public GenericException (String message, String traceback) : base(message)
		{
			this.Traceback = traceback;
		}

		public override String ToString ()
		{
			return String.Format ("Agnos.GenericException with remote backtrace:\n{0}\n{1}" + 
			                      "\n------------------- end of remote traceback -------------------\n{2}", 
			                      Message, Traceback, StackTrace);
		}
	}

	public static class Protocol
	{
		public const byte CMD_PING = 0;
		public const byte CMD_INVOKE = 1;
		public const byte CMD_QUIT = 2;
		public const byte CMD_DECREF = 3;
		public const byte CMD_INCREF = 4;
		public const byte CMD_GETINFO = 5;

		public const byte REPLY_SUCCESS = 0;
		public const byte REPLY_PROTOCOL_ERROR = 1;
		public const byte REPLY_PACKED_EXCEPTION = 2;
		public const byte REPLY_GENERIC_EXCEPTION = 3;

		public const int INFO_META = 0;
		public const int INFO_GENERAL = 1;
		public const int INFO_FUNCTIONS = 2;
		public const int INFO_FUNCCODES = 3;

		public const int AGNOS_MAGIC = 0x5af30cf7;

		public abstract class BaseProcessor : Packers.ISerializer
		{
			protected struct Cell
			{
				public int refcount;
				public Object obj;

				public Cell (Object obj)
				{
					refcount = 1;
					this.obj = obj;
				}
				public void incref ()
				{
					refcount += 1;
				}
				public bool decref ()
				{
					refcount -= 1;
					return refcount <= 0;
				}
			}

			private Dictionary<long, Cell> cells;
			private ObjectIDGenerator idGenerator;
			private int compacting_counter = 0;
			private const int COMPACTING_THRESHOLD = 2000;

			public BaseProcessor ()
			{
				idGenerator = new ObjectIDGenerator ();
				cells = new Dictionary<long, Cell> ();
			}

			public long store (Object obj)
			{
				if (obj == null) {
					return -1;
				}
				long id = idGenerator.getID (obj);
				Cell cell;
				if (cells.TryGetValue (id, out cell)) {
					//cell.incref();
				} else {
					cells.Add (id, new Cell (obj));
				}
				return id;
			}

			public Object load (long id)
			{
				if (id < 0) {
					return null;
				}
				return cells[id].obj;
			}

			protected void decref (long id)
			{
				Cell cell;
				if (cells.TryGetValue (id, out cell)) {
					if (cell.decref ()) {
						cells.Remove (id);
						compacting_counter += 1;
					}
					if (compacting_counter > COMPACTING_THRESHOLD) {
						compacting_counter = 0;
						idGenerator.Compact ();
					}
				}
			}

			protected void incref (long id)
			{
				Cell cell;
				if (cells.TryGetValue (id, out cell)) {
					cell.incref ();
				}
			}

			protected void sendProtocolError (ITransport transport, ProtocolError exc)
			{
				Packers.Int8.pack (REPLY_PROTOCOL_ERROR, transport);
				Packers.Str.pack (exc.ToString (), transport);
			}

			protected void sendGenericException (ITransport transport, GenericException exc)
			{
				Packers.Int8.pack (REPLY_GENERIC_EXCEPTION, transport);
				Packers.Str.pack (exc.Message, transport);
				Packers.Str.pack (exc.Traceback, transport);
			}

			public void process (ITransport transport)
			{
				int seq = transport.BeginRead ();
				byte cmdid = (byte)(Packers.Int8.unpack (transport));
				
				transport.BeginWrite (seq);
				
				try {
					switch (cmdid) {
					case CMD_INVOKE:
						processInvoke (transport, seq);
						break;
					case CMD_DECREF:
						processDecref (transport, seq);
						break;
					case CMD_INCREF:
						processIncref (transport, seq);
						break;
					case CMD_GETINFO:
						processGetInfo (transport, seq);
						break;
					case CMD_PING:
						processPing (transport, seq);
						break;
					case CMD_QUIT:
						processQuit (transport, seq);
						break;
					default:
						throw new ProtocolError ("unknown command code: " + cmdid);
					}
				} catch (ProtocolError exc) {
					transport.Reset ();
					sendProtocolError (transport, exc);
				} catch (GenericException exc) {
					transport.Reset ();
					sendGenericException (transport, exc);
				} catch (Exception ex) {
					transport.CancelWrite ();
					throw ex;
				} finally {
					transport.EndRead ();
				}
				transport.EndWrite ();
			}

			protected void processDecref (ITransport transport, int seq)
			{
				long id = (long)(Packers.Int64.unpack (transport));
				decref (id);
			}

			protected void processIncref (ITransport transport, int seq)
			{
				long id = (long)(Packers.Int64.unpack (transport));
				incref (id);
			}

			protected void processQuit (ITransport transport, int seq)
			{
			}

			protected void processPing (ITransport transport, int seq)
			{
				String message = (String)(Packers.Str.unpack (transport));
				Packers.Int8.pack (REPLY_SUCCESS, transport);
				Packers.Str.pack (message, transport);
			}

			protected void processGetInfo (ITransport transport, int seq)
			{
				int code = (int)(Packers.Int32.unpack (transport));
				HeteroMap info = new HeteroMap();
				
				switch (code) {
				case INFO_GENERAL:
					processGetGeneralInfo (info);
					break;
				case INFO_FUNCTIONS:
					processGetFunctionsInfo (info);
					break;
				case INFO_FUNCCODES:
					processGetFunctionCodes (info);
					break;
				case INFO_META:
				default:
					info["INFO_META"] = INFO_META;
					info["INFO_GENERAL"] = INFO_GENERAL;
					info["INFO_FUNCTIONS"] = INFO_FUNCTIONS;
					info["INFO_FUNCCODE"] = INFO_FUNCCODES;
					break;
				}
				
				Packers.Int8.pack (REPLY_SUCCESS, transport);
				Packers.builtinHeteroMapPacker.pack(info, transport);
			}

			protected abstract void processGetGeneralInfo (HeteroMap info);
			protected abstract void processGetFunctionsInfo (HeteroMap info);
			protected abstract void processGetFunctionCodes (HeteroMap info);

			protected abstract void processInvoke (ITransport transport, int seq);
		}

		public class ClientUtils
		{
			protected enum ReplySlotType
			{
				SLOT_EMPTY,
				SLOT_DISCARDED,
				SLOT_VALUE,
				SLOT_EXCEPTION
			}

			protected class ReplySlot
			{
				public ReplySlotType type;
				public Object value;

				public ReplySlot (Packers.AbstractPacker packer)
				{
					type = ReplySlotType.SLOT_EMPTY;
					value = packer;
				}
			}

			public ITransport transport;
			protected int seq;
			protected Dictionary<int, ReplySlot> replies;
			protected Dictionary<long, WeakReference> proxies;
			protected Dictionary<int, Packers.AbstractPacker> packedExceptionsMap;

			public ClientUtils (ITransport transport, Dictionary<int, Packers.AbstractPacker> packedExceptionsMap)
			{
				this.transport = transport;
				this.packedExceptionsMap = packedExceptionsMap;
				seq = 0;
				replies = new Dictionary<int, ReplySlot> (128);
				proxies = new Dictionary<long, WeakReference> ();
			}

			public void Close ()
			{
				if (transport != null) {
					transport.Close ();
					transport = null;
				}
			}

			protected int getSeq ()
			{
				lock (this) {
					seq += 1;
					return seq;
				}
			}

			public object GetProxy (long objref)
			{
				WeakReference weak;
				if (proxies.TryGetValue (objref, out weak)) {
					if (weak.IsAlive) {
						return weak.Target;
					}
					proxies.Remove (objref);
				}
				return null;
			}

			public void CacheProxy (long objref, object proxy)
			{
				proxies[objref] = new WeakReference (proxy);
			}

			public int BeginCall (int funcid, Packers.AbstractPacker packer)
			{
				int seq = getSeq ();
				transport.BeginWrite (seq);
				Packers.Int8.pack (CMD_INVOKE, transport);
				Packers.Int32.pack (funcid, transport);
				replies[seq] = new ReplySlot (packer);
				return seq;
			}

			public void EndCall ()
			{
				transport.EndWrite ();
			}

			public void CancelCall ()
			{
				transport.CancelWrite ();
			}

			/*public int TunnelRequest (byte[] blob)
			{
				int seq = getSeq ();
				transport.BeginWrite (seq);
				transport.Write (blob, 0, blob.Length);
				transport.EndWrite ();
				replies[seq] = new ReplySlot (Packers.MockupPacker);
				return seq;
			}*/

			public void Decref (long id)
			{
				int seq = getSeq ();
				transport.BeginWrite (seq);
				try {
					Packers.Int8.pack (CMD_DECREF, transport);
					Packers.Int64.pack (id, transport);
					transport.EndWrite ();
				} catch (Exception) {
					// swallow exceptions
					transport.CancelWrite ();
				}
			}

			public int Ping (string payload, int msecs)
			{
				DateTime t0 = DateTime.Now;
				int seq = getSeq ();
				transport.BeginWrite (seq);
				Packers.Int8.pack (CMD_PING, transport);
				Packers.Str.pack (payload, transport);
				transport.EndWrite ();
				replies[seq] = new ReplySlot (Packers.Str);
				string reply;
				try {
					reply = (String)GetReply (seq, msecs);
				} catch (TimeoutException ex) {
					DiscardReply (seq);
					throw ex;
				}
				TimeSpan dt = DateTime.Now - t0;
				if (reply != payload) {
					throw new ProtocolError ("reply does not match payload!");
				}
				return dt.Milliseconds;
			}

			public HeteroMap GetServiceInfo (int code)
			{
				int seq = getSeq ();
				transport.BeginWrite (seq);
				Packers.Int8.pack (CMD_GETINFO, transport);
				Packers.Int32.pack (code, transport);
				transport.EndWrite ();
				replies[seq] = new ReplySlot (Packers.builtinHeteroMapPacker);
				return (HeteroMap)GetReply (seq);
			}

			protected PackedException loadPackedException ()
			{
				int clsid = (int)Packers.Int32.unpack (transport);
				Packers.AbstractPacker packer;
				if (!packedExceptionsMap.TryGetValue (clsid, out packer)) {
					throw new ProtocolError ("unknown exception class id: " + clsid);
				}
				return (PackedException)packer.unpack (transport);
			}

			protected ProtocolError loadProtocolError ()
			{
				String message = (string)Packers.Str.unpack (transport);
				return new ProtocolError (message);
			}

			protected GenericException loadGenericException ()
			{
				string message = (string)Packers.Str.unpack (transport);
				string traceback = (string)Packers.Str.unpack (transport);
				return new GenericException (message, traceback);
			}

			public void ProcessIncoming (int msecs)
			{
				int seq = transport.BeginRead (msecs);
				
				try {
					int code = (byte)(Packers.Int8.unpack (transport));
					ReplySlot slot;
					
					if (!replies.TryGetValue (seq, out slot) || 
							(slot.type != ReplySlotType.SLOT_EMPTY && slot.type != ReplySlotType.SLOT_DISCARDED)) {
						throw new ProtocolError ("invalid reply sequence: " + seq);
					}
					Packers.AbstractPacker packer = (Packers.AbstractPacker)slot.value;
					bool discard = (slot.type == ReplySlotType.SLOT_DISCARDED);
					
					switch (code) {
					case REPLY_SUCCESS:
						if (packer == null) {
							slot.value = null;
						} 
						/*else if (packer == Packers.MockupPacker) {
							slot.value = transport.ReadAll ();
						}*/
						else {
							slot.value = packer.unpack (transport);
						}
						slot.type = ReplySlotType.SLOT_VALUE;
						break;
					case REPLY_PROTOCOL_ERROR:
						throw (ProtocolError)loadProtocolError ();
					case REPLY_PACKED_EXCEPTION:
						slot.type = ReplySlotType.SLOT_EXCEPTION;
						slot.value = loadPackedException ();
						break;
					case REPLY_GENERIC_EXCEPTION:
						slot.type = ReplySlotType.SLOT_EXCEPTION;
						slot.value = loadGenericException ();
						break;
					default:
						throw new ProtocolError ("unknown reply code: " + code);
					}
					
					if (discard) {
						replies.Remove (seq);
					}
				} finally {
					transport.EndRead ();
				}
			}

			public bool IsReplyReady (int seq)
			{
				ReplySlot slot = replies[seq];
				return slot.type == ReplySlotType.SLOT_VALUE || slot.type == ReplySlotType.SLOT_EXCEPTION;
			}

			public void DiscardReply (int seq)
			{
				ReplySlot slot;
				if (replies.TryGetValue (seq, out slot)) {
					if (IsReplyReady (seq)) {
						replies.Remove (seq);
					} else {
						slot.type = ReplySlotType.SLOT_DISCARDED;
					}
				}
			}

			protected readonly DateTime infinity = new DateTime (9999, 12, 31);

			protected ReplySlot WaitReply (int seq, int msecs)
			{
				ReplySlot slot;
				DateTime tend = infinity;
				int msecs2 = -1;
				if (msecs >= 0) {
					tend = DateTime.Now + TimeSpan.FromMilliseconds (msecs);
				}
				
				while (!IsReplyReady (seq)) {
					if (msecs >= 0) {
						TimeSpan remaining = tend - DateTime.Now;
						if (remaining < TimeSpan.Zero) {
							throw new TimeoutException ("reply did not arrive in time");
						}
						msecs2 = remaining.Milliseconds;
					}
					ProcessIncoming (msecs2);
				}
				
				slot = replies[seq];
				replies.Remove (seq);
				return slot;
			}

			public Object GetReply (int seq, int msecs)
			{
				ReplySlot slot = WaitReply (seq, msecs);
				if (slot.type == ReplySlotType.SLOT_VALUE) {
					return slot.value;
				} else if (slot.type == ReplySlotType.SLOT_EXCEPTION) {
					throw (Exception)slot.value;
				} else {
					throw new ApplicationException ("invalid slot type: " + slot.type);
				}
			}

			public Object GetReply (int seq)
			{
				return GetReply (seq, -1);
			}
		}

		public class BaseClient
		{
			public ClientUtils _utils;
			
	        public HeteroMap GetServiceInfo(int code)
	        {
	        		return _utils.GetServiceInfo(code);
	        }
	        
	        /*public byte[] TunnelRequest(byte[] blob)
	        {
	        		int seq = _utils.TunnelRequest(blob);
				return (byte[])_utils.GetReply(seq);
			}*/
		}
		
	}
}
