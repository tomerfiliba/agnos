#ifndef AGNOS_PROTOCOL_HPP_INCLUDED
#define AGNOS_PROTOCOL_HPP_INCLUDED

#include "objtypes.hpp"
#include "utils.hpp"
#include "packers.hpp"
#include "transports.hpp"
#include "heteromap.hpp"


namespace agnos
{
	DEFINE_EXCEPTION(PackedException);
	DEFINE_EXCEPTION(ProtocolError);
	DEFINE_EXCEPTION2(WrongAgnosVersion, ProtocolError);
	DEFINE_EXCEPTION2(WrongServiceName, ProtocolError);
	DEFINE_EXCEPTION2(IncompatibleServiceVersion, ProtocolError);

	class GenericException : public std::exception
	{
	protected:
		mutable string formatted;
	public:
		string message;
		string traceback;

		GenericException(const string& message, const string& traceback) :
			message(message), traceback(traceback)
		{
		}

		~GenericException() throw()
		{
		}

		virtual const char* what() const throw ()
		{
			formatted = "agnos.GenericException: ";
			formatted += message;
			formatted += " with remote backtrace:\n";
			formatted += traceback;
			formatted += "\t------------------- end of remote traceback -------------------";
			return formatted.c_str();
		}
	};

	namespace protocol
	{
		using agnos::transports::ITransport;
		using namespace agnos::packers;

		const int8_t CMD_PING = 0;
		const int8_t CMD_INVOKE = 1;
		const int8_t CMD_QUIT = 2;
		const int8_t CMD_DECREF = 3;
		const int8_t CMD_INCREF = 4;
		const int8_t CMD_GETINFO = 5;

		const int8_t REPLY_SUCCESS = 0;
		const int8_t REPLY_PROTOCOL_ERROR = 1;
		const int8_t REPLY_PACKED_EXCEPTION = 2;
		const int8_t REPLY_GENERIC_EXCEPTION = 3;

		const int32_t INFO_META = 0;
		const int32_t INFO_GENERAL = 1;
		const int32_t INFO_FUNCTIONS = 2;
		const int32_t INFO_FUNCCODES = 3;

		class BaseProcessor : protected ISerializer
		{
		protected:
			struct Cell
			{
				int refcount;
				any value;

				Cell(any value) : refcount(1), value(value)
				{
				}
				Cell(const Cell& other) : refcount(other.refcount), value(other.value)
				{
				}
				inline void incref()
				{
					refcount += 1;
				}
				inline bool decref()
				{
					refcount -= 1;
					return refcount <= 0;
				}
			};

			typedef map<objref_t, Cell> objmap_t;
			objmap_t objmap;
			shared_ptr<ITransport> transport;

			void incref(objref_t id);
			void decref(objref_t id);
			void send_protocol_error(const ProtocolError& exc);
			void send_generic_exception(const GenericException& exc);
			void process_decref(int32_t seq);
			void process_incref(int32_t seq);
			void process_quit(int32_t seq);
			void process_ping(int32_t seq);
			void process_get_info(int32_t seq);

			objref_t store(objref_t oid, any obj);
			any load(objref_t oid);

			virtual void process_get_general_info(HeteroMap& map) = 0;
			virtual void process_get_functions_info(HeteroMap& map) = 0;
			virtual void process_get_function_codes(HeteroMap& map) = 0;
			virtual void process_invoke(int32_t seq) = 0;

		public:
			BaseProcessor(shared_ptr<ITransport> transport);
			void process();
			void serve();
		};


		class IProcessorFactory
		{
		public:
			virtual shared_ptr<BaseProcessor> create(shared_ptr<ITransport> transport) = 0;
		};

		//////////////////////////////////////////////////////////////////////

		enum ReplySlotType
		{
			SLOT_EMPTY,
			SLOT_DISCARDED,
			SLOT_VALUE,
			SLOT_GENERIC_EXCEPTION,
			SLOT_PACKED_EXCEPTION,
		};

		struct ReplySlot
		{
			ReplySlotType type;
			any value;

			ReplySlot(IPacker * packer) :
				type(SLOT_EMPTY), value(packer)
			{
			}
		};

		class ClientUtils
		{
		public:
			map<int32_t, IPacker*> packed_exceptions_map;

		protected:
			map<int32_t, shared_ptr<ReplySlot> > replies;
			map<objref_t, any> proxies;
			volatile int32_t _seq;

			int32_t get_seq();
			PackedException load_packed_exception();
			ProtocolError load_protocol_error();
			GenericException load_generic_exception();

		public:
			shared_ptr<ITransport> transport;

			ClientUtils(shared_ptr<ITransport> transport);

			void close();

			template<typename T> shared_ptr<T> get_proxy(objref_t oid)
			{
				weak_ptr<T> wp = any_cast< weak_ptr<T> >(*map_get(proxies, oid));
				if (wp.expired()) {
					proxies.erase(oid);
				}
				return wp.lock();
			}

			template<typename T> void cache_proxy(shared_ptr<T> proxy)
			{
				map_put(proxies, proxy->_oid, any(weak_ptr<T>(proxy)));
			}

			void decref(objref_t oid);

			int32_t begin_call(int32_t funcid, IPacker& packer);
			void end_call();
			void cancel_call();

			int ping(string payload, int msecs);
			shared_ptr<HeteroMap> get_service_info(int code);

			void process_incoming(int32_t msecs);
			bool is_reply_ready(int32_t seq);
			void discard_reply(int32_t seq);
			shared_ptr<ReplySlot> wait_reply(int32_t seq, int msecs);
			any get_reply(int32_t seq, int msecs = -1);

			template<typename T> inline T get_reply_as(int32_t seq, int msecs = -1)
			{
				return any_cast<T>(get_reply(seq, msecs));
			}
		};

		class BaseClient
		{
		public:
			ClientUtils _utils;

			BaseClient(shared_ptr<ITransport> transport);
			shared_ptr<HeteroMap> get_service_info(int code);
		};

	}
}







#endif // AGNOS_PROTOCOL_HPP_INCLUDED
