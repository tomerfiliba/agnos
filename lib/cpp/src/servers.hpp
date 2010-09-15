#ifndef AGNOS_SERVERS_HPP_INCLUDED
#define AGNOS_SERVERS_HPP_INCLUDED

#include "objtypes.hpp"
#include "utils.hpp"
#include "transports.hpp"
#include "transport_factories.hpp"
#include "protocol.hpp"


namespace agnos
{
	namespace servers
	{
		using agnos::protocol::BaseProcessor;
		using agnos::transports::ITransport;
		using agnos::transports::factories::ITransportFactory;
		using agnos::transports::factories::SocketTransportFactory;


		class BaseServer
		{
		protected:
			BaseProcessor& processor;
			ITransportFactory& transport_factory;

			static void serve_client(BaseProcessor& processor, ITransport& transport);
			virtual void accept_client(ITransport& transport) = 0;

		public:
			BaseServer(BaseProcessor& processor, ITransportFactory& transport_factory);
			virtual void serve();
		};

		//////////////////////////////////////////////////////////////////////

		class SimpleServer : public BaseServer
		{
		protected:
			virtual void accept_client(ITransport& transport);
		public:
			SimpleServer(BaseProcessor& processor, ITransportFactory& transport_factory);
		};

		//////////////////////////////////////////////////////////////////////

		class ThreadedServer : public BaseServer
		{
		protected:
			virtual void accept_client(ITransport& transport);
		public:
			ThreadedServer(BaseProcessor& processor, ITransportFactory& transport_factory);
		};

		//////////////////////////////////////////////////////////////////////

		class LibraryModeServer : public BaseServer
		{
		protected:
			virtual void accept_client(ITransport& transport);
		public:
			LibraryModeServer(BaseProcessor& processor);
			LibraryModeServer(BaseProcessor& processor, SocketTransportFactory& transport_factory);
			virtual void serve();
		};

		//////////////////////////////////////////////////////////////////////

		class CmdlineServer
		{
		protected:
			BaseProcessor& processor;
		public:
			CmdlineServer(BaseProcessor& processor);
			int main(int argc, const char* argv[]);
		};


	}
}



#endif // AGNOS_SERVERS_HPP_INCLUDED
