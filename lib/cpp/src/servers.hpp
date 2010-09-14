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


		DEFINE_EXCEPTION(SwitchError);

		class BaseServer
		{
		public:
			typedef shared_ptr<BaseProcessor> (*ProcessorFactory)(shared_ptr<ITransport>);

		protected:
			ProcessorFactory processor_factory;
			shared_ptr<ITransportFactory> transport_factory;

			virtual void serve_client(shared_ptr<BaseProcessor> proc) = 0;

		public:
			BaseServer(ProcessorFactory processor_factory, shared_ptr<ITransportFactory> transport_factory);
			virtual void serve();
			virtual void close();
		};


		//////////////////////////////////////////////////////////////////////

		class SimpleServer : public BaseServer
		{
		protected:
			virtual void serve_client(shared_ptr<BaseProcessor> proc);

		public:
			SimpleServer(ProcessorFactory processor_factory, shared_ptr<ITransportFactory> transport_factory);
		};

		//////////////////////////////////////////////////////////////////////

		class ThreadedServer : public BaseServer
		{
		protected:
			vector<shared_ptr<boost::thread> > threads;

			virtual void serve_client(shared_ptr<BaseProcessor> proc);

		public:
			ThreadedServer(ProcessorFactory processor_factory, shared_ptr<ITransportFactory> transport_factory);
		};

		//////////////////////////////////////////////////////////////////////

		class LibraryModeServer : public BaseServer
		{
		protected:
			virtual void serve_client(shared_ptr<BaseProcessor> proc);

		public:
			LibraryModeServer(ProcessorFactory processor_factory);
			LibraryModeServer(ProcessorFactory processor_factory, shared_ptr<SocketTransportFactory> transport_factory);
			virtual void serve();
		};

		//////////////////////////////////////////////////////////////////////

		class CmdlineServer
		{
		protected:
			BaseServer::ProcessorFactory processor_factory;

		public:
			CmdlineServer(BaseServer::ProcessorFactory processor_factory);
			int main(int argc, const char* argv[]);
		};


	}
}



#endif // AGNOS_SERVERS_HPP_INCLUDED
