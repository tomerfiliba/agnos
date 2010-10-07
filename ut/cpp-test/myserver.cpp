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

	shared_ptr<Address> get_address(const string& country, const string& city, const string& street, int32_t num)
	{
		return shared_ptr<Address>(new Address(country, city, street, num + 1));
	}

	shared_ptr<Address> modify_address(const Address& addr)
	{
		return shared_ptr<Address>(new Address(addr.country, addr.city, addr.street, addr.num * 2));
	}

};


int main(int argc, const char * argv[])
{
	ProcessorFactory processor_factory(shared_ptr<IHandler>(new Handler()));

	agnos::servers::CmdlineServer server(processor_factory);
	return server.main(argc, argv);
}

