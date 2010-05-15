using System;
using System.Collections.Generic;
using System.Text;
using System.Net;
using System.IO;
using System.Runtime.Serialization;


namespace Agnos
{
    public abstract class PackedException : Exception
    {
        public PackedException()
        {
        }
    }

    public class ProtocolError : Exception
    {
        public ProtocolError(String message)
            : base(message)
        {
        }
    }

    public class GenericException : Exception
    {
        public String Traceback;

        public GenericException(String message, String traceback)
            : base(message)
        {
            this.Traceback = traceback;
        }

        public String toString()
        {
            return "Agnos.GenericException with remote backtrace:\n" + Traceback +
            "\t------------------- end of remote traceback -------------------";
        }
    }

    public static class Protocol
    {
        public const int CMD_PING = 0;
        public const int CMD_INVOKE = 1;
        public const int CMD_QUIT = 2;
        public const int CMD_DECREF = 3;
        public const int CMD_INCREF = 4;

        public const int REPLY_SUCCESS = 0;
        public const int REPLY_PROTOCOL_ERROR = 1;
        public const int REPLY_PACKED_EXCEPTION = 2;
        public const int REPLY_GENERIC_EXCEPTION = 3;

        public abstract class BaseProcessor : Packers.ISerializer
        {
            protected struct Cell
            {
                public int refcount;
                public Object obj;

                public Cell(Object obj)
                {
                    refcount = 1;
                    this.obj = obj;
                }
                public void incref()
                {
                    refcount += 1;
                }
                public bool decref()
                {
                    refcount -= 1;
                    return refcount <= 0;
                }
            }

            private Dictionary<long, Cell> cells;
            private ObjectIDGenerator idGenerator;
            private int compacting_counter = 0;
            private const int COMPACTING_THRESHOLD = 2000;
            private MemoryStream sendBuffer;

            public BaseProcessor()
            {
                idGenerator = new ObjectIDGenerator();
                cells = new Dictionary<long, Cell>();
                sendBuffer = new MemoryStream(128 * 1024);
            }

            public long store(Object obj)
            {
                if (obj == null)
                {
                    return -1;
                }
                long id = idGenerator.getID(obj);
                Cell cell;
                if (cells.TryGetValue(id, out cell))
                {
                    //cell.incref();
                }
                else
                {
                    cells.Add(id, new Cell(obj));
                }
                return id;
            }

            public Object load(long id)
            {
                if (id < 0)
                {
                    return null;
                }
                return cells[id].obj;
            }

            protected void decref(long id)
            {
                Cell cell;
                if (cells.TryGetValue(id, out cell))
                {
                    if (cell.decref())
                    {
                        cells.Remove(id);
                        compacting_counter += 1;
                    }
                    if (compacting_counter > COMPACTING_THRESHOLD)
                    {
                        compacting_counter = 0;
                        idGenerator.Compact();
                    }
                }
            }

            protected void incref(long id)
            {
                Cell cell;
                if (cells.TryGetValue(id, out cell))
                {
                    cell.incref();
                }
            }

            protected void send_protocol_error(Stream outStream, int seq, ProtocolError exc)
            {
                Packers.Int32.pack(seq, outStream);
                Packers.Int8.pack((byte)REPLY_PROTOCOL_ERROR, outStream);
                Packers.Str.pack(exc.ToString(), outStream);
            }

            protected void send_generic_exception(Stream outStream, int seq, GenericException exc)
            {
                Packers.Int32.pack(seq, outStream);
                Packers.Int8.pack((byte)REPLY_GENERIC_EXCEPTION, outStream);
                Packers.Str.pack(exc.ToString(), outStream);
                Packers.Str.pack(exc.Traceback, outStream);
            }

            public void process(Stream inStream, Stream outStream)
            {
                int seq = (int)(Packers.Int32.unpack(inStream));
                int cmdid = (byte)(Packers.Int8.unpack(inStream));

                sendBuffer.Position = 0;
                sendBuffer.SetLength(0);
                try
                {
                    switch (cmdid)
                    {
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
                catch (ProtocolError exc)
                {
                    sendBuffer.Position = 0;
                    sendBuffer.SetLength(0);
                    send_protocol_error(sendBuffer, seq, exc);
                }
                catch (GenericException exc)
                {
                    sendBuffer.Position = 0;
                    sendBuffer.SetLength(0);
                    send_generic_exception(sendBuffer, seq, exc);
                }

                sendBuffer.WriteTo(outStream);
                outStream.Flush();
            }

            protected void process_decref(Stream inStream, Stream outStream, int seq)
            {
                long id = (long)(Packers.Int64.unpack(inStream));
                decref(id);
            }

            protected void process_incref(Stream inStream, Stream outStream, int seq)
            {
                long id = (long)(Packers.Int64.unpack(inStream));
                incref(id);
            }

            protected void process_quit(Stream inStream, Stream outStream, int seq)
            {
            }

            protected void process_ping(Stream inStream, Stream outStream, int seq)
            {
                String message = (String)(Packers.Str.unpack(inStream));
                Packers.Int32.pack(seq, outStream);
                Packers.Int8.pack(REPLY_SUCCESS, outStream);
                Packers.Str.pack(message, outStream);
            }

            abstract protected void process_invoke(Stream inStream, Stream outStream, int seq);
        }

        public abstract class BaseClient : IDisposable
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

                public ReplySlot(Packers.IPacker packer)
                {
                    type = ReplySlotType.SLOT_EMPTY;
                    value = packer;
                }
            }

            protected Stream _inStream;
            protected Stream _outStream;
            protected MemoryStream _sendBuffer;
            protected int _seq;
            protected Dictionary<int, ReplySlot> _replies;
            protected Dictionary<long, WeakReference> _proxies;

            public BaseClient(Stream inStream, Stream outStream)
            {
                _inStream = inStream;
                _outStream = outStream;
                _sendBuffer = new MemoryStream(128 * 1024);
                _seq = 0;
                _replies = new Dictionary<int, ReplySlot>(128);
                _proxies = new Dictionary<long, WeakReference>();
            }

            public BaseClient(Transports.ITransport transport) :
                this(transport.getInputStream(), transport.getOutputStream())
            {
            }

            ~BaseClient()
            {
                Dispose();
            }

            public void Close()
            {
                if (_inStream != null)
                {
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

            protected int _get_seq()
            {
                lock (this)
                {
                    _seq += 1;
                    return _seq;
                }
            }

            protected object _get_proxy(long objref)
            {
                WeakReference weak;
                if (_proxies.TryGetValue(objref, out weak))
                {
                    if (weak.IsAlive)
                    {
                        return weak.Target;
                    }
                    _proxies.Remove(objref);
                }
                return null;
            }

            protected void _decref(long id)
            {
                int seq = _get_seq();
                try
                {
                    Packers.Int32.pack(seq, _outStream);
                    Packers.Int8.pack(CMD_DECREF, _outStream);
                    Packers.Int64.pack(id, _outStream);
                }
                catch (Exception)
                {
                    // ignored
                }
            }

            protected int _send_invocation(Stream stream, int funcid, Packers.IPacker packer)
            {
                int seq = _get_seq();
                Packers.Int32.pack(seq, stream);
                Packers.Int8.pack(CMD_INVOKE, stream);
                Packers.Int32.pack(funcid, stream);
                _replies.Add(seq, new ReplySlot(packer));
                return seq;
            }

            protected abstract PackedException _load_packed_exception();

            protected ProtocolError _load_protocol_error()
            {
                String message = (string)Packers.Str.unpack(_inStream);
                return new ProtocolError(message);
            }

            protected GenericException _load_generic_exception()
            {
                string message = (string)Packers.Str.unpack(_inStream);
                string traceback = (string)Packers.Str.unpack(_inStream);
                return new GenericException(message, traceback);
            }

            protected bool _process_incoming(int timeout_msecs)
            {
                int seq = (int)(Packers.Int32.unpack(_inStream));
                int code = (byte)(Packers.Int8.unpack(_inStream));

                ReplySlot slot;
                if (!_replies.TryGetValue(seq, out slot) || (slot.type != ReplySlotType.SLOT_EMPTY && slot.type != ReplySlotType.SLOT_DISCARDED))
                {
                    throw new ProtocolError("invalid reply sequence: " + seq);
                }
                Packers.IPacker packer = (Packers.IPacker)slot.value;

                switch (code)
                {
                    case REPLY_SUCCESS:
                        if (packer == null)
                        {
                            slot.value = null;
                        }
                        else
                        {
                            slot.value = packer.unpack(_inStream);
                        }
                        slot.type = ReplySlotType.SLOT_VALUE;
                        break;
                    case REPLY_PROTOCOL_ERROR:
                        throw (ProtocolError)_load_protocol_error();
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

            protected bool _is_reply_ready(int seq)
            {
                ReplySlot slot;
                if (_replies.TryGetValue(seq, out slot))
                {
                    return slot.type == ReplySlotType.SLOT_VALUE || slot.type == ReplySlotType.SLOT_EXCEPTION;
                }
                else
                {
                    throw new ArgumentException("seq does not exist");
                }
            }

            protected ReplySlot _wait_reply(int seq, int timeout_msecs)
            {
                ReplySlot slot;
                while (!_is_reply_ready(seq))
                {
                    _process_incoming(timeout_msecs);
                }
                _replies.TryGetValue(seq, out slot);
                _replies.Remove(seq);
                return slot;
            }

            protected Object _get_reply(int seq, int timeout_msecs)
            {
                ReplySlot slot = _wait_reply(seq, timeout_msecs);
                if (slot.type == ReplySlotType.SLOT_VALUE)
                {
                    return slot.value;
                }
                else if (slot.type == ReplySlotType.SLOT_EXCEPTION)
                {
                    throw (Exception)slot.value;
                }
                else
                {
                    throw new Exception("invalid slot type: " + slot.type);
                }
            }

            protected Object _get_reply(int seq)
            {
                return _get_reply(seq, -1);
            }
        }
    }

}
