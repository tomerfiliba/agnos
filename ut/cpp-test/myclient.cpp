#include <iostream>
#include <cstdlib>
#include "bindings/FeatureTest_client_bindings.hpp"

using namespace std;
using namespace agnos;
using namespace FeatureTest::ClientBindings;


int main(int argc, const char * argv[])
{
	if (argc != 3) {
		cerr << "usage: " << argv[0] << " <host> <port>" << endl;
		return 1;
	}

	Client client = Client::connect_sock(argv[1], (unsigned short)::atoi(argv[2]));
	cout << "IDL_MAGIC = " << client.get_service_info(agnos::protocol::INFO_GENERAL)->get_as<string>("IDL_MAGIC") << endl;
	return 0;
}
