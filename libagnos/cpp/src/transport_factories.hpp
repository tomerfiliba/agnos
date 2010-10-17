#ifndef AGNOS_TRANSPORT_FACTORIES_HPP_INCLUDED
#define AGNOS_TRANSPORT_FACTORIES_HPP_INCLUDED

#include "objtypes.hpp"
#include "transports.hpp"
#include "utils.hpp"
#include <boost/asio.hpp>


namespace agnos
{
	namespace transports
	{
		namespace factories
		{
			using boost::asio::ip::tcp;

			class ITransportFactory : public boost::noncopyable
			{
			public:
				virtual void close() = 0;
				virtual shared_ptr<ITransport> accept() = 0;
			};

			//////////////////////////////////////////////////////////////////

			class SocketTransportFactory : public ITransportFactory
			{
			public:
				static const int DEFAULT_BACKLOG = 10;
				tcp::endpoint endpoint;
				shared_ptr<tcp::acceptor> acceptor;

				SocketTransportFactory(unsigned short port, int backlog = DEFAULT_BACKLOG);
				SocketTransportFactory(const char * host, unsigned short port, int backlog = DEFAULT_BACKLOG);
				SocketTransportFactory(const tcp::endpoint& endpoint, int backlog = DEFAULT_BACKLOG);

				virtual void close();
				shared_ptr<ITransport> accept();
			};

		}
	}
}


#endif // AGNOS_TRANSPORT_FACTORIES_HPP_INCLUDED