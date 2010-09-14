#include <stdio.h>
#include <cstdlib>
#include <string>
#include <algorithm>
#include "servers.hpp"


namespace agnos
{
	namespace servers
	{
		//////////////////////////////////////////////////////////////////////
		// BaseServer
		//////////////////////////////////////////////////////////////////////

		BaseServer::BaseServer(ProcessorFactory processor_factory, shared_ptr<ITransportFactory> transport_factory) :
				processor_factory(processor_factory), transport_factory(transport_factory)
		{
		}

		void BaseServer::close()
		{
			transport_factory->close();
		}

		void BaseServer::serve()
		{
			while (true) {
				shared_ptr<ITransport> transport = transport_factory->accept();
				shared_ptr<BaseProcessor> proc = processor_factory(transport);
				serve_client(proc);
			}
		}

		//////////////////////////////////////////////////////////////////////
		// SimpleServer
		//////////////////////////////////////////////////////////////////////

		SimpleServer::SimpleServer(ProcessorFactory processor_factory, shared_ptr<ITransportFactory> transport_factory) :
				BaseServer(processor_factory, transport_factory)
		{
		}

		void SimpleServer::serve_client(shared_ptr<BaseProcessor> proc)
		{
			proc->serve();
		}

		//////////////////////////////////////////////////////////////////////
		// ThreadedServer
		//////////////////////////////////////////////////////////////////////

		ThreadedServer::ThreadedServer(ProcessorFactory processor_factory, shared_ptr<ITransportFactory> transport_factory) :
				BaseServer(processor_factory, transport_factory)
		{
		}

		static void _threadproc(shared_ptr<BaseProcessor> proc)
		{
			proc->serve();
		}

		void ThreadedServer::serve_client(shared_ptr<BaseProcessor> proc)
		{
			shared_ptr<boost::thread> thrd(new boost::thread(_threadproc, proc));
			threads.push_back(thrd);
		}

		//////////////////////////////////////////////////////////////////////
		// LibraryModeServer
		//////////////////////////////////////////////////////////////////////
		LibraryModeServer::LibraryModeServer(ProcessorFactory processor_factory) :
				BaseServer(processor_factory,
					shared_ptr<SocketTransportFactory>(new SocketTransportFactory("127.0.0.1", 0)))
		{
		}

		LibraryModeServer::LibraryModeServer(ProcessorFactory processor_factory, shared_ptr<SocketTransportFactory> transport_factory) :
				BaseServer(processor_factory, transport_factory)
		{
		}

		void LibraryModeServer::serve_client(shared_ptr<BaseProcessor> proc)
		{
			throw std::runtime_error("LibraryModeServer::serve_client not implemented");
		}

		void LibraryModeServer::serve()
		{
			shared_ptr<SocketTransportFactory> factory = boost::shared_static_cast<SocketTransportFactory>(transport_factory);
			std::cout << "AGNOS" << std::endl;
			std::cout << factory->endpoint.address().to_string() << std::endl;
			std::cout << factory->endpoint.port() << std::endl;
			std::cout.flush();
			::fclose(::stdout);

			shared_ptr<ITransport> transport = factory->accept();
			factory->close();

			shared_ptr<BaseProcessor> proc = processor_factory(transport);
			proc->serve();
		}


		//////////////////////////////////////////////////////////////////////
		// CmdlineServer
		//////////////////////////////////////////////////////////////////////

		enum ServingModes
		{
			MODE_SIMPLE,
			MODE_THREADED,
			MODE_LIB,
		};

		CmdlineServer::CmdlineServer(BaseServer::ProcessorFactory processor_factory) :
				processor_factory(processor_factory)
		{
		}

		int CmdlineServer::main(int argc, const char* argv[])
		{
			ServingModes mode = MODE_SIMPLE;
			string host = "127.0.0.1";
			unsigned short port = 0;

			for (int i = 0; i < argc; i++) {
				string arg = argv[i];
				if (arg.compare("-m") == 0) {
					i += 1;
					if (i >= argc) {
						throw SwitchError("-h requires an argument");
					}
					arg = argv[i];
					std::transform(arg.begin(), arg.end(), arg.begin(), ::tolower);
					if (arg.compare("lib") == 0 || arg.compare("library") == 0) {
						mode = MODE_LIB;
					}
					else if (arg.compare("simple") == 0) {
						mode = MODE_SIMPLE;
					}
					else if (arg.compare("threaded") == 0) {
						mode = MODE_THREADED;
					}
					else {
						throw SwitchError("invalid server mode: " + arg);
					}
				}
				else if (arg.compare("-h") == 0) {
					i += 1;
					if (i >= argc) {
						throw SwitchError("-h requires an argument");
					}
					host = argv[i];
				}
				else if (arg.compare("-p") == 0) {
					i += 1;
					if (i >= argc) {
						throw SwitchError("-p requires an argument");
					}
					port = (unsigned short)::atoi(argv[i]);
				}
				else {
					throw SwitchError("invalid cmdline switch");
				}
			}

			scoped_ptr<BaseServer> server;
			shared_ptr<SocketTransportFactory> transport_factory;

			switch (mode)
			{
			case MODE_SIMPLE:
				if (port == 0) {
					throw SwitchError("simple server requires specifying a port");
				}
				transport_factory.reset(new SocketTransportFactory(host.c_str(), port));
				server.reset(new SimpleServer(processor_factory, transport_factory));
				break;

			case MODE_THREADED:
				if (port == 0) {
					throw SwitchError("threaded server requires specifying a port");
				}
				transport_factory.reset(new SocketTransportFactory(host.c_str(), port));
				server.reset(new ThreadedServer(processor_factory, transport_factory));
				break;

			case MODE_LIB:
				transport_factory.reset(new SocketTransportFactory(host.c_str(), port));
				server.reset(new LibraryModeServer(processor_factory, transport_factory));
				break;

			default:
				throw SwitchError("invalid server mode");
			}

			server->serve();
			return 0;
		}

	}
}
