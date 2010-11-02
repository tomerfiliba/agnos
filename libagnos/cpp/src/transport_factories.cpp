//////////////////////////////////////////////////////////////////////////////
// Part of the Agnos RPC Framework
//    http://agnos.sourceforge.net
//
// Copyright 2010, International Business Machines Corp.
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
