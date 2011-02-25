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

			/**
			 * a factory for transports
			 */
			class ITransportFactory : public boost::noncopyable
			{
			public:
				/**
				 * closes the factory and releases any operating system
				 * resources it holds (e,g., listening socket)
				 */
				virtual void close() = 0;

				/**
				 * accepts a new transport instance. this method would block
				 * until a connection request arrives
				 */
				virtual shared_ptr<ITransport> accept() = 0;
			};

			//////////////////////////////////////////////////////////////////

			/**
			 * listener-socket-based transport factory
			 */
			class SocketTransportFactory : public ITransportFactory
			{
			public:
				static const int DEFAULT_BACKLOG = 10;
				tcp::endpoint endpoint;
				shared_ptr<tcp::acceptor> acceptor;

				SocketTransportFactory(unsigned short port, int backlog = DEFAULT_BACKLOG);
				SocketTransportFactory(const char * host, unsigned short port, int backlog = DEFAULT_BACKLOG);
				SocketTransportFactory(const tcp::endpoint& endpoint, int backlog = DEFAULT_BACKLOG);
				~SocketTransportFactory();

				virtual void close();
				shared_ptr<ITransport> accept();
			};

		}
	}
}


#endif // AGNOS_TRANSPORT_FACTORIES_HPP_INCLUDED
