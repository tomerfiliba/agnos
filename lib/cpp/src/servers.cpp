#include "servers.hpp"


namespace agnos
{
	namespace servers
	{
		//////////////////////////////////////////////////////////////////////
		// BaseServer
		//////////////////////////////////////////////////////////////////////

		BaseServer::BaseServer(BaseProcessor& processor, ITransportFactory& transport_factory) :
				processor(processor), transport_factory(transport_factory)
		{
		}

		void BaseServer::serve()
		{
			while (true) {
				shared_ptr<ITransport> transport = transport_factory.accept();
				accept_client(*transport);
			}
		}

		void BaseServer::serve_client(BaseProcessor& processor, ITransport& transport)
		{
			while (true) {
				processor.process(transport);
			}
			transport.close();
		}

		//////////////////////////////////////////////////////////////////////
		// SimpleServer
		//////////////////////////////////////////////////////////////////////

		SimpleServer::SimpleServer(BaseProcessor& processor, ITransportFactory& transport_factory) :
				BaseServer(processor, transport_factory)
		{
		}

		void SimpleServer::accept_client(ITransport& transport)
		{
			serve_client(processor, transport);
		}

		//////////////////////////////////////////////////////////////////////
		// CmdlineServer
		//////////////////////////////////////////////////////////////////////

		enum ServingModes
		{
			SIMPLE,
			THREADED,
			LIB
		};

	}
}
