#include <iostream>
#include "bindings/simple_client_bindings.hpp"

using namespace std;
using namespace agnos;
using namespace simple::ClientBindings;


void foo(const string& x)
{
	cout << x << endl;
}


int main(int argc, const char * argv[])
{
	/*if (argc != 3) {
		cerr << "usage: " << argv[0] << " <host> <port>" << endl;
		return 1;
	}*/

	SubprocClient client("./myserver");

	/*cout << "result = " << client.add(5, 6) << endl;

	shared_ptr<Address> addr = client.get_address("israel", "tel aviv", "menahem begin", 132);
	cout << "city = " << addr->city << endl;
	cout << "num = " << addr->num << endl;

	shared_ptr<Address> addr2 = client.modify_address(*addr);
	cout << "num = " << addr2->num << endl;*/

	/*shared_ptr<HeteroMap> hm = client.get_service_info(agnos::protocol::INFO_FUNCTIONS);
	HeteroMap& hm2 = hm->get_as<HeteroMap>(900012);
	cout << hm2.get_as<string>("name") << endl;*/

	HeteroMap hm;
	string x("world");
	hm.put(11, x);
	const_cast<char*>(x.data())[1] = 'u';
	hm.put(22, x);

	cout << hm.get_as<string>(11) << endl;
	cout << hm.get_as<string>(22) << endl;


	return 0;
}
