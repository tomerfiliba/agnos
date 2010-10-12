#include "protocol.hpp"
#include <boost/interprocess/detail/atomic.hpp>


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

		void BaseProcessor::send_protocol_error(const ProtocolError& exc)
		{
			Int8Packer::pack(REPLY_PROTOCOL_ERROR, *transport);
			StringPacker::pack(exc.message, *transport);
		}

		void BaseProcessor::send_generic_exception(const GenericException& exc)
		{
			Int8Packer::pack(REPLY_GENERIC_EXCEPTION, *transport);
			StringPacker::pack(exc.message, *transport);
			StringPacker::pack(exc.traceback, *transport);
		}

		void BaseProcessor::process_decref(int32_t seq)
		{
			objref_t oid;
			Int64Packer::unpack(oid, *transport);
			decref(oid);
		}

		void BaseProcessor::process_incref(int32_t seq)
		{
			objref_t oid;
			Int64Packer::unpack(oid, *transport);
			incref(oid);
		}

		void BaseProcessor::process_quit(int32_t seq)
		{
		}

		void BaseProcessor::process_ping(int32_t seq)
		{
			string message;
			StringPacker::unpack(message, *transport);
			Int8Packer::pack(REPLY_SUCCESS, *transport);
			StringPacker::pack(message, *transport);
		}

		void BaseProcessor::process_get_info(int32_t seq)
		{
			int32_t code;
			Int32Packer::unpack(code, *transport);
			HeteroMap map;

			switch (code) {
			case INFO_GENERAL:
				DEBUG_LOG("INFO_GENERAL");
				process_get_general_info(map);
				break;
			case INFO_FUNCTIONS:
				DEBUG_LOG("INFO_FUNCTIONS");
				process_get_functions_info(map);
				break;
			case INFO_FUNCCODES:
				DEBUG_LOG("INFO_FUNCCODES");
				process_get_function_codes(map);
				break;
			case INFO_META:
				DEBUG_LOG("INFO_META");
				// fall-through
			default:
				map.put("INFO_META", INFO_META);
				map.put("INFO_GENERAL", INFO_GENERAL);
				map.put("INFO_FUNCTIONS", INFO_FUNCTIONS);
				map.put("INFO_FUNCCODES", INFO_FUNCCODES);
				break;
			}

			Int8Packer::pack(REPLY_SUCCESS, *transport);
			packers::builtin_heteromap_packer.pack(map, *transport);
		}

		objref_t BaseProcessor::store(objref_t oid, any obj)
		{
			map_put(objmap, oid, Cell(obj));
			return oid;
		}

		any BaseProcessor::load(objref_t oid)
		{
			objmap_t::const_iterator it = objmap.find(oid);
			if (it == objmap.end()) {
				THROW_FORMATTED(ProtocolError, "invalid object reference: " << oid);
			}
			return it->second.value;
		}

		struct _TransportEndRead
		{
			shared_ptr<ITransport> transport;
			_TransportEndRead(shared_ptr<ITransport> transport) : transport(transport)
			{
			}
			~_TransportEndRead()
			{
				transport->end_read();
			}
		};

		BaseProcessor::BaseProcessor(shared_ptr<ITransport> transport) :
				objmap(), transport(transport)
		{
		}

		void BaseProcessor::process()
		{
			int32_t seq = transport->begin_read();
			_TransportEndRead finalizer(transport);
			int8_t cmdid;
			Int8Packer::unpack(cmdid, *transport);

			transport->begin_write(seq);
			try {
				switch (cmdid) {
				case CMD_INVOKE:
					process_invoke(seq);
					break;
				case CMD_DECREF:
					process_decref(seq);
					break;
				case CMD_INCREF:
					process_incref(seq);
					break;
				case CMD_GETINFO:
					process_get_info(seq);
					break;
				case CMD_PING:
					process_ping(seq);
					break;
				case CMD_QUIT:
					process_quit(seq);
					break;
				default:
					THROW_FORMATTED(ProtocolError, "unknown command code: " << cmdid);
				}
			} catch (ProtocolError exc) {
				DEBUG_LOG("got a ProtocolError: " << exc.what());
				transport->reset();
				send_protocol_error(exc);
			} catch (GenericException exc) {
				DEBUG_LOG("got a GenericException: " << exc.what());
				transport.reset();
				send_generic_exception(exc);
			} catch (std::exception exc) {
				DEBUG_LOG("got an unknown exception: " << exc.what());
				DEBUG_LOG("typeinfo = " << typeid(exc).name() );
				transport->cancel_write();
				throw exc;
			}

			transport->end_write();
		}


		struct _TransportClose
		{
			shared_ptr<ITransport> transport;
			_TransportClose(shared_ptr<ITransport> transport) : transport(transport)
			{
			}
			~_TransportClose()
			{
				transport->close();
			}
		};


		void BaseProcessor::serve()
		{
			// automatically close the transport at exit
			_TransportClose finalizer(transport);

			try {
				while (true) {
					process();
				}
			}
			catch (transports::TransportEOFError& ex) {
				// this is expected
				DEBUG_LOG("got an EOF");
			}
			catch (transports::TransportError& ex) {
				// this might happen
				DEBUG_LOG("got a TransportError: " << ex.what());
			}
		}

		void BaseProcessor::close()
		{
			transport->close();
		}


		//////////////////////////////////////////////////////////////////////
		// ClientUtils
		//////////////////////////////////////////////////////////////////////

		ClientUtils::ClientUtils(shared_ptr<ITransport> transport) :
				packed_exceptions_map(),
				transport(transport),
				replies(),
				proxies(),
				_seq(0)
		{
		}

		int32_t ClientUtils::get_seq()
		{
			return boost::interprocess::detail::atomic_inc32((boost::uint32_t*)&_seq);
		}

		PackedException ClientUtils::load_packed_exception()
		{
			int32_t clsid;
			Int32Packer::unpack(clsid, *transport);
			IPacker ** packer = map_get(packed_exceptions_map, clsid, false);
			if (packer == NULL) {
				THROW_FORMATTED(ProtocolError, "unknown exception class id: " << clsid);
			}
			return (**packer).unpack_as<PackedException>(*transport);
		}

		ProtocolError ClientUtils::load_protocol_error()
		{
			string message;
			StringPacker::unpack(message, *transport);
			return ProtocolError(message);
		}

		GenericException ClientUtils::load_generic_exception()
		{
			string message;
			StringPacker::unpack(message, *transport);
			string traceback;
			StringPacker::unpack(traceback, *transport);
			return GenericException(message, traceback);
		}

		void ClientUtils::close()
		{
			transport->close();
		}

		void ClientUtils::decref(objref_t oid)
		{
			int32_t seq = get_seq();
			transport->begin_write(seq);
			Int8Packer::pack(CMD_DECREF, *transport);
			Int64Packer::pack(oid, *transport);
			transport->end_write();
		}

		int32_t ClientUtils::begin_call(int32_t funcid, IPacker& packer, bool shared)
		{
			int32_t seq = get_seq();
			transport->begin_write(seq);
			Int8Packer::pack(CMD_INVOKE, *transport);
			Int32Packer::pack(funcid, *transport);
			map_put(replies, seq, shared_ptr<ReplySlot>(new ReplySlot(shared, &packer)));
			return seq;
		}

		void ClientUtils::end_call()
		{
			transport->end_write();
		}

		void ClientUtils::cancel_call()
		{
			transport->cancel_write();
		}

		int ClientUtils::ping(string payload, int msecs)
		{
			int seq = get_seq();
			transport->begin_write(seq);
			Int8Packer::pack(CMD_PING, *transport);
			StringPacker::pack(payload, *transport);
			transport->end_write();
			map_put(replies, seq, shared_ptr<ReplySlot>(new ReplySlot(false, &string_packer)));
			string reply = get_reply_as<string>(seq, msecs);
			if (reply != payload) {
				throw ProtocolError("reply does not match payload!");
			}
			return 0;
		}

		shared_ptr<HeteroMap> ClientUtils::get_service_info(int code)
		{
			int32_t seq = get_seq();
			transport->begin_write(seq);
			Int8Packer::pack(CMD_GETINFO, *transport);
			Int32Packer::pack(code, *transport);
			transport->end_write();
			map_put(replies, seq, shared_ptr<ReplySlot>(new ReplySlot(true, &builtin_heteromap_packer)));
			return get_reply_as< shared_ptr<HeteroMap> >(seq);
		}

		void ClientUtils::process_incoming(int32_t msecs)
		{
			int32_t seq = transport->begin_read();
			_TransportEndRead finalizer(transport);

			int8_t code;
			Int8Packer::unpack(code, *transport);
			shared_ptr<ReplySlot> * slot = map_get(replies, seq, false);

			if (slot == NULL || ((**slot).type != SLOT_PACKER && (**slot).type != SLOT_PACKER_SHARED && (**slot).type != SLOT_DISCARDED)) {
				THROW_FORMATTED(ProtocolError, "invalid reply sequence: " << seq);
			}
			bool discard = ((**slot).type == SLOT_DISCARDED);
			IPacker* packer = any_cast<IPacker*>((**slot).value);

			switch (code) {
			case REPLY_SUCCESS:
				if (packer == NULL) {
					(**slot).value = NULL;
				}
				else if ((**slot).type == SLOT_PACKER) {
					(**slot).value = packer->unpack_any(*transport);
				}
				else if ((**slot).type == SLOT_PACKER_SHARED) {
					(**slot).value = packer->unpack_shared(*transport);
				}
				else {
					THROW_FORMATTED(std::runtime_error, "invalid slot type: " << (**slot).type);
				}
				(**slot).type = SLOT_VALUE;
				break;
			case REPLY_PROTOCOL_ERROR:
				throw load_protocol_error();
			case REPLY_PACKED_EXCEPTION:
				(**slot).type = SLOT_PACKED_EXCEPTION;
				(**slot).value = load_packed_exception();
				break;
			case REPLY_GENERIC_EXCEPTION:
				(**slot).type = SLOT_GENERIC_EXCEPTION;
				(**slot).value = load_generic_exception();
				break;
			default:
				THROW_FORMATTED(ProtocolError, "unknown reply code: " << code);
			}

			if (discard) {
				replies.erase(seq);
			}
		}

		bool ClientUtils::is_reply_ready(int32_t seq)
		{
			shared_ptr<ReplySlot> slot = *map_get(replies, seq);
			return (slot->type == SLOT_VALUE || slot->type == SLOT_GENERIC_EXCEPTION || slot->type == SLOT_PACKED_EXCEPTION);
		}

		void ClientUtils::discard_reply(int32_t seq)
		{
			shared_ptr<ReplySlot> * slot = map_get(replies, seq, false);
			if (slot == NULL) {
				return;
			}
			if ((**slot).type == SLOT_VALUE || (**slot).type == SLOT_GENERIC_EXCEPTION || (**slot).type == SLOT_PACKED_EXCEPTION) {
				replies.erase(seq);
			}
			else {
				(**slot).type = SLOT_DISCARDED;
			}
		}

		shared_ptr<ReplySlot> ClientUtils::wait_reply(int32_t seq, int msecs)
		{
			while (!is_reply_ready(seq)) {
				process_incoming(msecs);
			}
			shared_ptr<ReplySlot> slot = *map_get(replies, seq);
			replies.erase(seq);
			return slot;
		}

		any ClientUtils::get_reply(int32_t seq, int msecs)
		{
			shared_ptr<ReplySlot> slot = wait_reply(seq, msecs);

			DEBUG_LOG("slot type = " << slot->type);
			DEBUG_LOG("value type = " << slot->value.type().name());

			if (slot->type == SLOT_VALUE) {
				return slot->value;
			}
			else if (slot->type == SLOT_PACKED_EXCEPTION) {
				throw any_cast<PackedException>(slot->value);
			}
			else if (slot->type == SLOT_GENERIC_EXCEPTION) {
				throw any_cast<GenericException>(slot->value);
			}
			else {
				THROW_FORMATTED(std::runtime_error, "invalid slot type: " << slot->type);
			}
		}

		////////////////////////////////////////////////////////////////////////
		// BaseClient
		////////////////////////////////////////////////////////////////////////
		BaseClient::BaseClient(shared_ptr<ITransport> transport) :
				_utils(transport)
		{
		}

		shared_ptr<HeteroMap> BaseClient::get_service_info(int code)
		{
			return _utils.get_service_info(code);
		}

	}
}
