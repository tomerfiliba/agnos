using System;
using System.Collections.Generic;
using System.Text;
using System.Net;
using System.IO;
using System.Runtime.Serialization;


namespace Agnos
{
	public abstract class PackedException : Exception {
		public PackedException() {
		}

		public PackedException(String message): base(message)
		{
		}

		public abstract void pack(Stream stream);
	}

	public class ProtocolError : Exception {
		public ProtocolError(String message): base(message)
		{
		}
	}

	public class GenericError : Exception {
		public String traceback;
		
		public GenericError(String message, String traceback) : base(message)
		{
			this.traceback = traceback;
		}
		
		public String toString()
		{
			return "Agnos.GenericError with remote backtrace:\n" + traceback + 
			"\t------------------- end of remote traceback -------------------"; 
		}
	}
	
	public static class Protocol
	{
		internal const int CMD_PING = 0;
		internal const int CMD_INVOKE = 1;
		internal const int CMD_QUIT = 2;
		internal const int CMD_DECREF = 3;
	
		internal const int REPLY_SUCCESS = 0;
		internal const int REPLY_PROTOCOL_ERROR = 1;
		internal const int REPLY_PACKED_ERROR = 2;
		internal const int REPLY_GENERIC_ERROR = 3;

		public abstract class BaseProcessor
		{
			protected struct Cell 
			{
				public int refcount;
				public Object obj;
		
				public Cell(Object obj) {
					refcount = 1;
					this.obj = obj;
				}
				public void incref() {
					refcount += 1;
				}
				public bool decref() {
					refcount -= 1;
					return refcount <= 0;
				}
			}

			private Dictionary<long, Cell> cells;
			private ObjectIDGenerator idGenerator;
			
			public BaseProcessor()
			{
				idGenerator = new ObjectIDGenerator();
				cells = new Dictionary<long, Cell>();
			}

			protected long store(Object obj) {
				long id = idGenerator.getID(obj);
				Cell cell;
				if (cells.TryGetValue(id, out cell)) {
					cell.incref();
				}
				else {
					cells.Add(id, new Cell(obj));
				}
				return id;
			}
	
			protected Object load(long id) {
				return cells[id].obj;
			}
	
			protected void decref(long id) {
				Cell cell;
				if (cells.TryGetValue(id, out cell)) {
					if (cell.decref()) {
						cells.Remove(id);
						//idGenerator.Compact();
					}
				}
			}
	
			protected void send_packed_exception(Stream outStream, int seq, PackedException exc) 
			{
				Packers.Int32.pack(seq, outStream);
				Packers.Int8.pack((byte)REPLY_PACKED_ERROR, outStream);
				exc.pack(outStream);
				outStream.Flush();
			}
	
			protected void send_protocol_error(Stream outStream, int seq, ProtocolError exc)
			{
				Packers.Int32.pack(seq, outStream);
				Packers.Int8.pack((byte)REPLY_PROTOCOL_ERROR, outStream);
				Packers.Str.pack(exc.ToString(), outStream);
				outStream.Flush();
			}
			
			protected void send_generic_error(Stream outStream, int seq, Exception exc)
			{
				Packers.Int32.pack(seq, outStream);
				Packers.Int8.pack((byte)REPLY_GENERIC_ERROR, outStream);
				Packers.Str.pack(exc.ToString(), outStream);
				Packers.Str.pack(exc.StackTrace, outStream);
				outStream.Flush();
			}
	
			public void process(Stream inStream, Stream outStream)
			{
				int seq = (int)(Packers.Int32.unpack(inStream));
				int cmdid = (byte)(Packers.Int8.unpack(inStream));
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
	
			protected void process_decref(Stream inStream, Stream outStream, int seq)
			{
				long id = (long)(Packers.Int64.unpack(inStream));
				decref(id);
			}
	
			protected void process_quit(Stream inStream, Stream outStream, int seq) 
			{
			}
	
			protected void process_ping(Stream inStream, Stream outStream, int seq)
			{
				String message = (String) (Packers.Str.unpack(inStream));
				Packers.Int32.pack(seq, outStream);
				Packers.Int8.pack(REPLY_SUCCESS, outStream);
				Packers.Str.pack(message, outStream);
				outStream.Flush();
			}
	
			abstract protected void process_invoke(Stream inStream, Stream outStream, int seq);
		}

		public abstract class BaseClient : IDisposable
		{
			protected Stream _inStream;
			protected Stream _outStream;
			protected int _seq;
	
			public BaseClient(Stream inStream, Stream outStream) {
				_inStream = inStream;
				_outStream = outStream;
				_seq = 0;
			}
	
			public BaseClient(Servers.ITransport transport) : 
				this(transport.getInputStream(), transport.getOutputStream())
			{
			}
			
			~BaseClient()
			{
				Dispose();
			}
	
			public void Close() 
			{
				if (_inStream != null) {
					_inStream.Close();
					_outStream.Close();
					_inStream = null;
					_outStream = null;
				}
			}
			
			public void Dispose()
			{
				Close();
				GC.SuppressFinalize(this);
			}
	
			protected int _get_seq() {
				lock (this) {
					_seq += 1;
					return _seq;
				}
			}
	
			protected void _decref(long id) {
				int seq = _get_seq();
				try {
					Packers.Int32.pack(seq, _outStream);
					Packers.Int8.pack(CMD_DECREF, _outStream);
					Packers.Int64.pack(id, _outStream);
				} catch (Exception) {
					// ignored
				}
			}
	
			protected int _cmd_invoke(int funcid)
			{
				int seq = _get_seq();
				Packers.Int32.pack(seq, _outStream);
				Packers.Int8.pack(CMD_INVOKE, _outStream);
				Packers.Int32.pack(funcid, _outStream);
				return seq;
			}
	
			protected abstract PackedException _load_packed_exception();
	
			protected ProtocolError _load_protocol_error()
			{
				String message = (string) Packers.Str.unpack(_inStream);
				return new ProtocolError(message);
			}
	
			protected GenericError _load_generic_error()
			{
				string message = (string) Packers.Str.unpack(_inStream);
				string traceback = (string) Packers.Str.unpack(_inStream);
				return new GenericError(message, traceback);
			}
	
			protected Object _read_reply(Packers.IPacker packer)
			{
				int seq = (int) (Packers.Int32.unpack(_inStream));
				int code = (byte) (Packers.Int8.unpack(_inStream));
				
				switch (code) {
					case REPLY_SUCCESS:
						if (packer == null) {
							return null;
						}
						else {
							return packer.unpack(_inStream);
						}
					case REPLY_PROTOCOL_ERROR:
						throw _load_protocol_error();
					case REPLY_PACKED_ERROR:
						throw _load_packed_exception();
					case REPLY_GENERIC_ERROR:
						throw _load_generic_error();
					default:
						throw new ProtocolError("unknown reply code: " + code);
				}
			}
		}
	}
	
}
