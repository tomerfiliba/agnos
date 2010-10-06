#include "bindings/simple_server_bindings.hpp"

using namespace agnos;
using namespace simple::ServerBindings;


class Handler : public IHandler
{
public:
	int32_t add(int a, int b)
	{
		return a + b;
	}

	shared_ptr<Address> get_address()
	{
		return shared_ptr<Address>(new Address("israel", "tel aviv", "menahem begin", 132));
	}
};


int main(int argc, const char * argv[])
{
	ProcessorFactory processor_factory(shared_ptr<IHandler>(new Handler()));

	agnos::servers::CmdlineServer server(processor_factory);
	return server.main(argc, argv);
}

