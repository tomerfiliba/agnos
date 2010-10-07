#include <iostream>
#include "bindings/simple_client_bindings.hpp"

using namespace std;
using namespace agnos;
using namespace simple::ClientBindings;


int main(int argc, const char * argv[])
{
	if (argc != 3) {
		cerr << "usage: " << argv[0] << " <host> <port>" << endl;
		return 1;
	}

	SocketClient client(argv[1], argv[2]);

	/*cout << "result = " << client.add(5, 6) << endl;

	shared_ptr<Address> addr = client.get_address("israel", "tel aviv", "menahem begin", 132);
	cout << "city = " << addr->city << endl;
	cout << "num = " << addr->num << endl;

	shared_ptr<Address> addr2 = client.modify_address(*addr);
	cout << "num = " << addr2->num << endl;*/

	shared_ptr<HeteroMap> hm = client.get_service_info(agnos::protocol::INFO_GENERAL);
	cout << hm->get_as<string>("IDL_MAGIC") << endl;

	return 0;
}
