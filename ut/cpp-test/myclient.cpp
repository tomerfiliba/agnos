#include <iostream>
#include "bindings/simple_client_bindings.hpp"

using namespace std;
using namespace agnos;
using namespace simple::ClientBindings;
using namespace agnos::packers;
using namespace agnos::protocol;


template<typename T> std::ostream& operator<< (std::ostream& stream, shared_ptr<T> obj)
{
	return stream << *obj;
}

int main(int argc, const char * argv[])
{
	SubprocClient client("./myserver");

	PersonProxy father = client.get_father();
	cout << "!!" << father << endl;
	cout << "!!" << father->get_full_name() << endl;
	cout << "!!" << father->get_dob() << endl;
	cout << "------------------------------------" << endl;
	PersonProxy child = father->give_birth("yakov buzaglo");
	cout << "!!" << child << endl;
	cout << "!!" << child->get_dob() << endl;
	cout << "------------------------------------" << endl;


	return 0;
}
