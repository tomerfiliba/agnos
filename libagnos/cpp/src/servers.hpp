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
		using agnos::protocol::IProcessorFactory;
		using agnos::transports::ITransport;
		using agnos::transports::factories::ITransportFactory;
		using agnos::transports::factories::SocketTransportFactory;


		DEFINE_EXCEPTION(SwitchError);

		/**
		 * base class for Agnos servers
		 */
		class BaseServer : public boost::noncopyable
		{
		protected:
			IProcessorFactory& processor_factory;
			shared_ptr<ITransportFactory> transport_factory;

			virtual void serve_client(shared_ptr<BaseProcessor> proc) = 0;

		public:
			/**
			 * instantiate a base server with a processor factory and a
			 * transport factory
			 */
			BaseServer(IProcessorFactory& processor_factory, shared_ptr<ITransportFactory> transport_factory);

			/**
			 * the server's main loop
			 */
			virtual void serve();

			/**
			 * closes the serves and disconnects all active clients
			 */
			virtual void close();
		};


		//////////////////////////////////////////////////////////////////////

		/**
		 * a server that supports only a single client at any point of time
		 */
		class SimpleServer : public BaseServer
		{
		protected:
			virtual void serve_client(shared_ptr<BaseProcessor> proc);

		public:
			SimpleServer(IProcessorFactory& processor_factory, shared_ptr<ITransportFactory> transport_factory);
		};

		//////////////////////////////////////////////////////////////////////

		/**
		 * a server that creates a separate thread to handle each client
		 */
		class ThreadedServer : public BaseServer
		{
		protected:
			vector<shared_ptr<boost::thread> > threads;

			virtual void serve_client(shared_ptr<BaseProcessor> proc);

		public:
			ThreadedServer(IProcessorFactory& processor_factory, shared_ptr<ITransportFactory> transport_factory);
		};

		//////////////////////////////////////////////////////////////////////

		/**
		 * the library mode server: when serve() is called, the server prints
		 * its details (host and port number) to stdout and waits for a single
		 * connection. when this connection terminates, serve() returns and
		 * the server process is expected to quit
		 */
		class LibraryModeServer : public BaseServer
		{
		protected:
			virtual void serve_client(shared_ptr<BaseProcessor> proc);

		public:
			LibraryModeServer(IProcessorFactory& processor_factory);
			LibraryModeServer(IProcessorFactory& processor_factory, shared_ptr<SocketTransportFactory> transport_factory);
			virtual void serve();
		};

		//////////////////////////////////////////////////////////////////////

		/**
		 * a simple entry point for an Agnos server process. it parses the
		 * command-line arguments and chooses the appropriate server to
		 * start
		 */
		class CmdlineServer : public boost::noncopyable
		{
		protected:
			IProcessorFactory& processor_factory;

		public:
			CmdlineServer(IProcessorFactory& processor_factory);
			int main(int argc, const char* argv[]);
		};


	}
}



#endif // AGNOS_SERVERS_HPP_INCLUDED
