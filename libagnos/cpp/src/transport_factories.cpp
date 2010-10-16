#include "transport_factories.hpp"


namespace agnos
{
	namespace transports
	{
		namespace factories
		{
			boost::asio::io_service the_io_service;

			static inline shared_ptr<tcp::acceptor> _connect(const tcp::endpoint& endpoint, int backlog)
			{
				shared_ptr<tcp::acceptor> acceptor(new tcp::acceptor(the_io_service));
				acceptor->open(endpoint.protocol());
				acceptor->set_option(tcp::acceptor::reuse_address(true));
				acceptor->bind(endpoint);
				acceptor->listen(backlog);
				return acceptor;
			}

			SocketTransportFactory::SocketTransportFactory(unsigned short port, int backlog) :
				endpoint(tcp::endpoint(tcp::v4(), port))
			{
				acceptor = _connect(endpoint, backlog);
			}

			SocketTransportFactory::SocketTransportFactory(const char * host, unsigned short	 port, int backlog) :
				endpoint(tcp::endpoint(boost::asio::ip::address::from_string(host), port))
			{
				acceptor = _connect(endpoint, backlog);
			}

			SocketTransportFactory::SocketTransportFactory(const tcp::endpoint& endpoint, int backlog) :
				endpoint(endpoint)
			{
				acceptor = _connect(endpoint, backlog);
			}

			void SocketTransportFactory::close()
			{
				acceptor->close();
			}

			shared_ptr<ITransport> SocketTransportFactory::accept()
			{
				DEBUG_LOG("accepting...");
				shared_ptr<tcp::iostream> sockstream(new tcp::iostream());
				acceptor->accept(*(sockstream->rdbuf()));
				shared_ptr<ITransport> trns(new SocketTransport(sockstream));
				DEBUG_LOG("accepted " << *trns);

				return trns;
			}
		}
	}
}
