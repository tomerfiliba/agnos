#include "protocol.hpp"


namespace agnos
{
	namespace protocol
	{
		//////////////////////////////////////////////////////////////////////
		// BaseProcessor
		//////////////////////////////////////////////////////////////////////
		void BaseProcessor::incref(objref_t id)
		{
			objmap_t::iterator it = objmap.find(id);
			if (it == objmap.end()) {
				return;
			}
			it->second.incref();
		}

		void BaseProcessor::decref(objref_t id)
		{
			objmap_t::iterator it = objmap.find(id);
			if (it == objmap.end()) {
				return;
			}
			if (it->second.decref()) {
				objmap.erase(it);
			}
		}

		void BaseProcessor::send_protocol_error(ITransport& transport, const ProtocolError& exc)
		{
			Int8Packer::pack(REPLY_PROTOCOL_ERROR, transport);
			StringPacker::pack(exc.message, transport);
		}

		void BaseProcessor::send_generic_exception(ITransport& transport, const GenericException& exc)
		{
			Int8Packer::pack(REPLY_GENERIC_EXCEPTION, transport);
			StringPacker::pack(exc.message, transport);
			StringPacker::pack(exc.traceback, transport);
		}

		void BaseProcessor::process_decref(ITransport& transport, int32_t seq)
		{
			objref_t oid;
			Int64Packer::unpack(oid, transport);
			decref(oid);
		}

		void BaseProcessor::process_incref(ITransport& transport, int32_t seq)
		{
			objref_t oid;
			Int64Packer::unpack(oid, transport);
			incref(oid);
		}

		void BaseProcessor::process_quit(ITransport& transport, int32_t seq)
		{
		}

		void BaseProcessor::process_ping(ITransport& transport, int32_t seq)
		{
			string message;
			StringPacker::unpack(message, transport);
			Int8Packer::pack(REPLY_SUCCESS, transport);
			StringPacker::pack(message, transport);
		}

		void BaseProcessor::process_get_info(ITransport& transport, int32_t seq)
		{
			int32_t code;
			Int32Packer::unpack(code, transport);
			HeteroMap map;

			switch (code) {
			case INFO_GENERAL:
				process_get_general_info(map);
				break;
			case INFO_FUNCTIONS:
				process_get_functions_info(map);
				break;
			case INFO_FUNCCODES:
				process_get_function_codes(map);
				break;
			case INFO_META:
			default:
				map.put("INFO_META", INFO_META);
				map.put("INFO_GENERAL", INFO_GENERAL);
				map.put("INFO_FUNCTIONS", INFO_FUNCTIONS);
				map.put("INFO_FUNCCODES", INFO_FUNCCODES);
				break;
			}

			Int8Packer::pack(REPLY_SUCCESS, transport);
			packers::builtin_heteromap_packer.pack(map, transport);
		}

		void BaseProcessor::store(objref_t oid, any obj)
		{
			map_put(objmap, oid, Cell(obj));
		}

		any BaseProcessor::load(objref_t oid)
		{
			objmap_t::const_iterator it = objmap.find(oid);
			if (it == objmap.end()) {
				throw ProtocolError("invalid object reference <oid>");
			}
			return it->second.value;
		}

		struct _TransportEndRead
		{
			ITransport& transport;
			_TransportEndRead(ITransport& transport) : transport(transport)
			{
			}
			~_TransportEndRead()
			{
				transport.end_read();
			}
		};

		BaseProcessor::BaseProcessor() : objmap()
		{
		}

		void BaseProcessor::process(ITransport& transport)
		{
			int32_t seq = transport.begin_read();
			_TransportEndRead finalizer(transport);
			int8_t cmdid;
			Int8Packer::unpack(cmdid, transport);

			transport.begin_write(seq);
			try {
				switch (cmdid) {
				case CMD_INVOKE:
					process_invoke(transport, seq);
					break;
				case CMD_DECREF:
					process_decref(transport, seq);
					break;
				case CMD_INCREF:
					process_incref(transport, seq);
					break;
				case CMD_GETINFO:
					process_get_info(transport, seq);
					break;
				case CMD_PING:
					process_ping(transport, seq);
					break;
				case CMD_QUIT:
					process_quit(transport, seq);
					break;
				default:
					throw ProtocolError("unknown command code: ");
				}
			} catch (ProtocolError exc) {
				transport.reset();
				send_protocol_error(transport, exc);
			} catch (GenericException exc) {
				transport.reset();
				send_generic_exception(transport, exc);
			} catch (std::exception exc) {
				transport.cancel_write();
				throw exc;
			}

			transport.end_write();
		}

		//////////////////////////////////////////////////////////////////////
		// ClientUtils
		//////////////////////////////////////////////////////////////////////

		int32_t ClientUtils::get_seq()
		{
			_seq += 1;
			return _seq;
		}

		PackedException ClientUtils::load_packed_exception()
		{
			int32_t clsid;
			Int32Packer::unpack(clsid, transport);
			IPacker ** packer = map_get(*packed_exceptions_map, clsid, false);
			if (packer == NULL) {
				throw ProtocolError("unknown exception class id: ");
			}
			return (**packer).unpack_as<PackedException>(transport);
		}

		ProtocolError ClientUtils::load_protocol_error()
		{
			string message;
			StringPacker::unpack(message, transport);
			return ProtocolError(message);
		}

		GenericException ClientUtils::load_generic_exception()
		{
			string message;
			StringPacker::unpack(message, transport);
			string traceback;
			StringPacker::unpack(traceback, transport);
			return GenericException(message, traceback);
		}

		ClientUtils::ClientUtils(ITransport& transport, packed_exceptions_map_type packed_exceptions_map) :
				packed_exceptions_map(packed_exceptions_map), transport(transport)
		{
		}

		void ClientUtils::close()
		{
			transport.close();
		}

		void ClientUtils::decref(objref_t oid)
		{
			int32_t seq = get_seq();
			transport.begin_write(seq);
			Int8Packer::pack(CMD_DECREF, transport);
			Int64Packer::pack(oid, transport);
			transport.end_write();
		}

		int32_t ClientUtils::begin_call(int32_t funcid, IPacker& packer)
		{
			int32_t seq = get_seq();
			transport.begin_write(seq);
			Int8Packer::pack(CMD_INVOKE, transport);
			Int32Packer::pack(funcid, transport);
			map_put(replies, seq, ReplySlot(&packer));
			return seq;
		}

		void ClientUtils::end_call()
		{
			transport.end_write();
		}

		void ClientUtils::cancel_call()
		{
			transport.cancel_write();
		}

		int ClientUtils::ping(string payload, int msecs)
		{
			int seq = get_seq();
			transport.begin_write(seq);
			Int8Packer::pack(CMD_PING, transport);
			StringPacker::pack(payload, transport);
			transport.end_write();
			map_put(replies, seq, ReplySlot(&string_packer));
			string reply = get_reply_as<string>(seq, msecs);
			if (reply != payload) {
				throw ProtocolError("reply does not match payload!");
			}
			return 0;
		}

		HeteroMap ClientUtils::get_service_info(int code)
		{
			int32_t seq = get_seq();
			transport.begin_write(seq);
			Int8Packer::pack(CMD_GETINFO, transport);
			Int32Packer::pack(code, transport);
			transport.end_write();
			map_put(replies, seq, ReplySlot(&builtin_heteromap_packer));
			return get_reply_as<HeteroMap>(seq);
		}

		void ClientUtils::process_incoming(int32_t msecs)
		{
		}

		bool ClientUtils::is_reply_ready(int32_t seq)
		{
			ReplySlot * slot = map_get(replies, seq);
			return (slot->type == SLOT_VALUE || slot->type == SLOT_GENERIC_EXCEPTION || slot->type == SLOT_PACKED_EXCEPTION);
		}

		void ClientUtils::discard_reply(int32_t seq)
		{
			ReplySlot* slot = map_get(replies, seq, false);
			if (slot == NULL) {
				return;
			}
			if (slot->type == SLOT_VALUE || slot->type == SLOT_GENERIC_EXCEPTION || slot->type == SLOT_PACKED_EXCEPTION) {
				replies.erase(seq);
			}
			else {
				slot->type = SLOT_DISCARDED;
			}
		}

		ReplySlot& ClientUtils::wait_reply(int32_t seq, int msecs)
		{
			return *map_get(replies, seq);
		}

		any ClientUtils::get_reply(int32_t seq, int msecs)
		{
			return 0;
		}
	}
}
