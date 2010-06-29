using System;
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

    public class HandshakeError : ProtocolError
    {
        public HandshakeError(String message)
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

        public override String ToString()
        {
            return String.Format("Agnos.GenericException with remote backtrace:\n{0}\n{1}" +
                                  "\n------------------- end of remote traceback -------------------\n{2}",
                                  Message, Traceback, StackTrace);
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

        public const int AGNOS_MAGIC = 0x5af30cf7;

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

            public BaseProcessor()
            {
                idGenerator = new ObjectIDGenerator();
                cells = new Dictionary<long, Cell>();
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

            protected void sendProtocolError(ITransport transport, ProtocolError exc)
            {
                Packers.Int8.pack((byte)REPLY_PROTOCOL_ERROR, transport);
                Packers.Str.pack(exc.ToString(), transport);
            }

            protected void sendGenericException(ITransport transport, GenericException exc)
            {
                Packers.Int8.pack((byte)REPLY_GENERIC_EXCEPTION, transport);
                Packers.Str.pack(exc.Message, transport);
                Packers.Str.pack(exc.Traceback, transport);
            }

            public void process(ITransport transport)
            {
                int seq = transport.BeginRead();
                int cmdid = (byte)(Packers.Int8.unpack(transport));

                transport.BeginWrite(seq);

                try
                {
                    switch (cmdid)
                    {
                        case CMD_INVOKE:
                            processInvoke(transport, seq);
                            break;
                        case CMD_DECREF:
                            processDecref(transport, seq);
                            break;
                        case CMD_INCREF:
                            processIncref(transport, seq);
                            break;
                        case CMD_QUIT:
                            processQuit(transport, seq);
                            break;
                        case CMD_PING:
                            processPing(transport, seq);
                            break;
                        default:
                            throw new ProtocolError("unknown command code: " + cmdid);
                    }
                }
                catch (ProtocolError exc)
                {
                    transport.Reset();
                    sendProtocolError(transport, exc);
                }
                catch (GenericException exc)
                {
                    transport.Reset();
                    sendGenericException(transport, exc);
                }
                catch (Exception ex)
                {
                    transport.CancelWrite();
                    throw ex;
                }
                finally
                {
                    transport.EndRead();
                }
                transport.EndWrite();
            }

            protected void processDecref(ITransport transport, int seq)
            {
                long id = (long)(Packers.Int64.unpack(transport));
                decref(id);
            }

            protected void processIncref(ITransport transport, int seq)
            {
                long id = (long)(Packers.Int64.unpack(transport));
                incref(id);
            }

            protected void processQuit(ITransport transport, int seq)
            {
            }

            protected void processPing(ITransport transport, int seq)
            {
                String message = (String)(Packers.Str.unpack(transport));
                Packers.Int8.pack(REPLY_SUCCESS, transport);
                Packers.Str.pack(message, transport);
            }

            protected abstract void processInvoke(ITransport transport, int seq);
        }

        public class BaseClientUtils
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

                public ReplySlot(Packers.BasePacker packer)
                {
                    type = ReplySlotType.SLOT_EMPTY;
                    value = packer;
                }
            }

            protected ITransport transport;
            protected int seq;
            protected Dictionary<int, ReplySlot> replies;
            protected Dictionary<long, WeakReference> proxies;
            protected Dictionary<int, Packers.BasePacker> packedExceptionsMap;

            public BaseClientUtils(ITransport transport, Dictionary<int, Packers.BasePacker> packedExceptionsMap)
            {
                this.transport = transport;
                this.packedExceptionsMap = packedExceptionsMap;
                seq = 0;
                replies = new Dictionary<int, ReplySlot>(128);
                proxies = new Dictionary<long, WeakReference>();
            }

            public void Close()
            {
                if (transport != null)
                {
                    transport.Close();
                    transport = null;
                }
            }

            protected int getSeq()
            {
                lock (this)
                {
                    seq += 1;
                    return seq;
                }
            }

            public object GetProxy(long objref)
            {
                WeakReference weak;
                if (proxies.TryGetValue(objref, out weak))
                {
                    if (weak.IsAlive)
                    {
                        return weak.Target;
                    }
                    proxies.Remove(objref);
                }
                return null;
            }

            public void CacheProxy(long objref, object proxy)
            {
                proxies[objref] = new WeakReference(proxy);
            }

            public void Decref(long id)
            {
                /*int seq = _get_seq ();
                try {
                    Packers.Int32.pack (seq, _outStream);
                    Packers.Int8.pack (CMD_DECREF, _outStream);
                    Packers.Int64.pack (id, _outStream);
                    _outStream.Flush ();
                } catch (Exception) {
                    // ignored
                }*/
            }

            public int BeginCall(int funcid, Packers.BasePacker packer)
            {
                int seq = getSeq();
                transport.BeginWrite(seq);
                Packers.Int8.pack(CMD_INVOKE, transport);
                Packers.Int32.pack(funcid, transport);
                replies[seq] = new ReplySlot(packer);
                return seq;
            }

            public void EndCall()
            {
                transport.EndWrite();
            }

            public void CancelCall()
            {
                transport.CancelWrite();
            }

            protected PackedException loadPackedException()
            {
                int clsid = (int)Packers.Int32.unpack(transport);
                Packers.BasePacker packer;
                if (!packedExceptionsMap.TryGetValue(clsid, out packer))
                {
                    throw new ProtocolError("unknown exception class id: " + clsid);
                }
                return (PackedException)packer.unpack(transport);
            }

            protected ProtocolError loadProtocolError()
            {
                String message = (string)Packers.Str.unpack(transport);
                return new ProtocolError(message);
            }

            protected GenericException loadGenericException()
            {
                string message = (string)Packers.Str.unpack(transport);
                string traceback = (string)Packers.Str.unpack(transport);
                return new GenericException(message, traceback);
            }

            public bool ProcessIncoming(int timeout_msecs)
            {
                int seq = transport.BeginRead();

                try
                {
                    int code = (byte)(Packers.Int8.unpack(transport));
                    ReplySlot slot;

                    if (!replies.TryGetValue(seq, out slot) ||
                        (slot.type != ReplySlotType.SLOT_EMPTY && slot.type != ReplySlotType.SLOT_DISCARDED))
                    {
                        throw new ProtocolError("invalid reply sequence: " + seq);
                    }
                    Packers.BasePacker packer = (Packers.BasePacker)slot.value;
                    bool discard = (slot.type == ReplySlotType.SLOT_DISCARDED);

                    switch (code)
                    {
                        case REPLY_SUCCESS:
                            if (packer == null)
                                slot.value = null;
                            else
                                slot.value = packer.unpack(transport);
                            slot.type = ReplySlotType.SLOT_VALUE;
                            break;
                        case REPLY_PROTOCOL_ERROR:
                            throw (ProtocolError)loadProtocolError();
                        case REPLY_PACKED_EXCEPTION:
                            slot.type = ReplySlotType.SLOT_EXCEPTION;
                            slot.value = loadPackedException();
                            break;
                        case REPLY_GENERIC_EXCEPTION:
                            slot.type = ReplySlotType.SLOT_EXCEPTION;
                            slot.value = loadGenericException();
                            break;
                        default:
                            throw new ProtocolError("unknown reply code: " + code);
                    }

                    if (discard)
                    {
                        replies.Remove(seq);
                    }
                }
                finally
                {
                    transport.EndRead();
                }

                return true;
            }

            public bool IsReplyReady(int seq)
            {
                ReplySlot slot = replies[seq];
                return slot.type == ReplySlotType.SLOT_VALUE ||
                    slot.type == ReplySlotType.SLOT_EXCEPTION;
            }

            public void DiscardReply(int seq)
            {
                ReplySlot slot;
                if (replies.TryGetValue(seq, out slot))
                {
                    if (IsReplyReady(seq))
                    {
                        replies.Remove(seq);
                    }
                    else
                    {
                        slot.type = ReplySlotType.SLOT_DISCARDED;
                    }
                }
            }

            protected ReplySlot WaitReply(int seq, int timeout_msecs)
            {
                ReplySlot slot;
                while (!IsReplyReady(seq))
                {
                    ProcessIncoming(timeout_msecs);
                }
                slot = replies[seq];
                replies.Remove(seq);
                return slot;
            }

            protected Object GetReply(int seq, int timeout_msecs)
            {
                ReplySlot slot = WaitReply(seq, timeout_msecs);
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
                    throw new ApplicationException("invalid slot type: " + slot.type);
                }
            }

            protected Object GetReply(int seq)
            {
                return GetReply(seq, -1);
            }
        }
    }

}
