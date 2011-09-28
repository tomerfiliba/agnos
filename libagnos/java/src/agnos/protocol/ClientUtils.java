//////////////////////////////////////////////////////////////////////////////
// Part of the Agnos RPC Framework
//    http://agnos.sourceforge.net
//
// Copyright 2011, International Business Machines Corp.
//                 Author: Tomer Filiba (tomerf@il.ibm.com)
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//    http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.
//////////////////////////////////////////////////////////////////////////////

package agnos.protocol;

import java.io.IOException;
import java.io.Closeable;
import java.lang.ref.WeakReference;
import java.util.HashMap;
import java.util.Map;
import java.util.logging.Logger;

import agnos.packers.AbstractPacker;
import agnos.packers.Builtin;
import agnos.transports.ITransport;
import agnos.util.HeteroMap;
import agnos.util.SimpleLogger;

/**
 * A collection of client-side utilities. Although this class is public, it is
 * not meant to be used directly.
 * 
 * @author Tomer Filiba
 */
public final class ClientUtils implements Closeable {
	protected enum ReplySlotType {
		SLOT_EMPTY(false), 
		SLOT_DISCARDED(false),
		SLOT_VALUE(true),
		SLOT_GENERIC_EXCEPTION(true),
		SLOT_PACKED_EXCEPTION(true);

		public final boolean ready;

		private ReplySlotType(boolean ready) {
			this.ready = ready;
		}
	}

	protected final class ReplySlot {
		public ReplySlotType type;
		public Object value;

		public ReplySlot(AbstractPacker packer) {
			type = ReplySlotType.SLOT_EMPTY;
			value = packer;
		}
	}

	protected final Map<Integer, AbstractPacker> packedExceptionsMap;
	protected final Map<Integer, ReplySlot> replies;
	protected final Map<Long, WeakReference<Object>> proxies;
	protected int _seq;
	public ITransport transport;
	protected Logger logger = SimpleLogger.getLogger("CLIENT");

	public ClientUtils(ITransport transport,
			Map<Integer, AbstractPacker> packedExceptionsMap)
			throws Exception {
		this.transport = transport;
		this.packedExceptionsMap = packedExceptionsMap;
		_seq = 0;
		replies = new HashMap<Integer, ReplySlot>(128);
		proxies = new HashMap<Long, WeakReference<Object>>();
	}

	public void close() throws IOException {
		if (transport != null) {
			transport.close();
			transport = null;
		}
	}

	protected synchronized int getSeq() {
		_seq += 1;
		return _seq;
	}

	public Object getProxy(Long objref) {
		WeakReference<Object> weak = proxies.get(objref);
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

	public void cacheProxy(Long objref, Object proxy) {
		proxies.put(objref, new WeakReference<Object>(proxy));
	}

	public int beginCall(int funcid, AbstractPacker packer)
			throws IOException {
		int seq = getSeq();
		logger.info("beginCall seq = " + seq + " func = " + funcid);
		transport.beginWrite(seq);
		Builtin.Int8.pack(constants.CMD_INVOKE, transport);
		Builtin.Int32.pack(funcid, transport);
		replies.put(seq, new ReplySlot(packer));
		return seq;
	}

	public void endCall() throws IOException {
		transport.endWrite();
		logger.info("endCall");
	}

	public void cancelCall() throws IOException {
		transport.cancelWrite();
		logger.info("cancelCall");
	}

	public void decref(long id) throws IOException {
		int seq = getSeq();
		logger.info("decref " + id);
		transport.beginWrite(seq);
		try {
			Builtin.Int8.pack(constants.CMD_DECREF, transport);
			Builtin.Int64.pack(id, transport);
			transport.endWrite();
		} catch (Exception ignored) {
			try {
				transport.cancelWrite();
			} catch (Exception ignored2) {
				// ignored
			}
		}
	}
	
	public int ping(String payload, int msecs) throws IOException,
			ProtocolException, PackedException, GenericException {
		// DateTime t0 = DateTime.Now;
		int seq = getSeq();
		transport.beginWrite(seq);
		Builtin.Int8.pack(constants.CMD_PING, transport);
		Builtin.Str.pack(payload, transport);
		transport.endWrite();
		replies.put(seq, new ReplySlot(Builtin.Str));
		String reply;
		// try {
		reply = (String) getReply(seq, msecs);
		// } catch (TimeoutException ex) {
		// DiscardReply (seq);
		// throw ex;
		// }
		// TimeSpan dt = DateTime.Now - t0;
		if (reply != payload) {
			throw new ProtocolException("reply does not match payload!");
		}
		// return dt.Milliseconds;
		return 0;
	}

	public HeteroMap getServiceInfo(int code) throws IOException,
			ProtocolException, PackedException, GenericException {
		int seq = getSeq();
		logger.info("getServiceInfo " + code);
		transport.beginWrite(seq);
		Builtin.Int8.pack(constants.CMD_GETINFO, transport);
		Builtin.Int32.pack(code, transport);
		transport.endWrite();
		replies.put(seq, new ReplySlot(Builtin.heteroMapPacker));
		return (HeteroMap) getReply(seq);
	}

	protected PackedException loadPackedException() throws IOException,
			ProtocolException {
		Integer clsid = (Integer) Builtin.Int32.unpack(transport);
		AbstractPacker packer = packedExceptionsMap.get(clsid);
		if (packer == null) {
			throw new ProtocolException("unknown exception class id: " + clsid);
		}
		return (PackedException) packer.unpack(transport);
	}

	protected ProtocolException loadProtocolException() throws IOException {
		String message = (String) Builtin.Str.unpack(transport);
		return new ProtocolException(message);
	}

	protected GenericException loadGenericException() throws IOException {
		String message = (String) Builtin.Str.unpack(transport);
		String traceback = (String) Builtin.Str.unpack(transport);
		return new GenericException(message, traceback);
	}

	public void processIncoming(int timeout_msecs) throws IOException,
			ProtocolException {
		logger.info("processIncoming");
		int seq = transport.beginRead();

		logger.info("processIncoming seq = " + seq);

		try {
			int code = (Byte) (Builtin.Int8.unpack(transport));
			ReplySlot slot = replies.get(seq);

			if (slot == null
					|| (slot.type != ReplySlotType.SLOT_EMPTY && slot.type != ReplySlotType.SLOT_DISCARDED)) {
				throw new ProtocolException("invalid reply sequence: " + seq);
			}
			boolean discard = (slot.type == ReplySlotType.SLOT_DISCARDED);
			AbstractPacker packer = (AbstractPacker) slot.value;

			switch (code) {
			case constants.REPLY_SUCCESS:
				if (packer == null) {
					slot.value = null;
				} else {
					slot.value = packer.unpack(transport);
				}
				slot.type = ReplySlotType.SLOT_VALUE;
				break;
			case constants.REPLY_PROTOCOL_EXCEPTION:
				throw (ProtocolException) (loadProtocolException().fillInStackTrace());
			case constants.REPLY_PACKED_EXCEPTION:
				slot.type = ReplySlotType.SLOT_PACKED_EXCEPTION;
				slot.value = loadPackedException();
				break;
			case constants.REPLY_GENERIC_EXCEPTION:
				slot.type = ReplySlotType.SLOT_GENERIC_EXCEPTION;
				slot.value = loadGenericException();
				break;
			default:
				throw new ProtocolException("unknown reply code: " + code);
			}

			if (discard) {
				replies.remove(seq);
			}
		} finally {
			transport.endRead();
		}
		logger.info("processIncoming finished " + seq);
	}

	public boolean isReplyReady(int seq) {
		ReplySlot slot = replies.get(seq);
		return slot.type.ready;
	}

	public void discardReply(int seq) {
		ReplySlot slot = replies.get(seq);
		if (slot == null) {
			return;
		}
		if (slot.type.ready) {
			replies.remove(seq);
		} else {
			slot.type = ReplySlotType.SLOT_DISCARDED;
		}
	}

	public ReplySlot waitReply(int seq, int msecs) throws IOException,
			ProtocolException {
		logger.info("waitReply seq = " + seq);
		while (!isReplyReady(seq)) {
			processIncoming(msecs);
		}
		return replies.remove(seq);
	}

	public Object getReply(int seq, int msecs) throws IOException,
			PackedException, GenericException, ProtocolException {
		ReplySlot slot = waitReply(seq, msecs);
		if (slot.type == ReplySlotType.SLOT_VALUE) {
			return slot.value;
		} else if (slot.type == ReplySlotType.SLOT_PACKED_EXCEPTION) {
			((PackedException) slot.value).fillInStackTrace();
			throw (PackedException) slot.value;
		} else if (slot.type == ReplySlotType.SLOT_GENERIC_EXCEPTION) {
			((GenericException) slot.value).fillInStackTrace();
			throw (GenericException) slot.value;
		} else {
			throw new AssertionError("invalid slot type: " + slot.type);
		}
	}

	public Object getReply(int seq) throws IOException, PackedException,
			GenericException, ProtocolException {
		return getReply(seq, -1);
	}
}