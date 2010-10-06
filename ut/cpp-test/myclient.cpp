#include <iostream>
#include <cstdlib>
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

	shared_ptr<Client> client = Client::connect_sock(argv[1], (unsigned short)::atoi(argv[2]));
	cout << "result = " << client->add(5, 6) << endl;

	shared_ptr<Address> addr = client->get_address("israel", "tel aviv", "menahem begin", 132);
	cout << "city = " << addr->city << endl;

	return 0;
}
