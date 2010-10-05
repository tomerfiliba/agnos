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
};


int main(int argc, const char * argv[])
{
	ProcessorFactory processor_factory(shared_ptr<IHandler>(new Handler()));

	agnos::servers::CmdlineServer server(processor_factory);
	return server.main(argc, argv);
}

