#include <iostream>
#include "bindings/FeatureTest_client_bindings.hpp"

using namespace std;
using namespace agnos;
using namespace FeatureTest::ClientBindings;


template<typename T> std::ostream& operator<< (std::ostream& stream, shared_ptr<T> obj)
{
	return stream << *obj;
}

int main(int argc, const char * argv[])
{
	//SubprocClient client("./myserver");
	if (argc != 3) {
		cerr << "usage: " << argv[0] << " <host> <port>" << endl;
	}
	SocketClient client(argv[1], argv[2]);
	client.assert_service_compatibility();

	PersonProxy NULL_PERSON_PROXY;

	cout << typeid(NULL_PERSON_PROXY).name() << endl;

	PersonProxy eve = client.Person.init("eve", NULL_PERSON_PROXY, NULL_PERSON_PROXY);
	PersonProxy adam = client.Person.init("adam", NULL_PERSON_PROXY, NULL_PERSON_PROXY);

	cout << eve << endl;
	cout << adam->get_name() << endl;

	eve->marry(adam);

	PersonProxy cain = client.Person.init("cain", adam, eve);

	if (cain->get_name()->compare("cain") != 0) {
		throw std::runtime_error("cain is not the name");
	}

    bool succ = true;
	try {
		adam->marry(eve);
	} catch (MartialStatusError& ex) {
		// okay
        succ = false;
	} catch (PackedException& ex) {
		// okay
		succ = false;
	}

    if (succ) {
        throw std::runtime_error("an exception should have been thrown!");
    }

	double thought = adam->think(17, 3.0);
    if (thought != (17/3.0)) {
		THROW_FORMATTED(std::runtime_error, "adam thinks wrong: " << thought);
    }

    succ = true;
    try {
		// division by zero does not throw in c++
		adam->think(17, 0);
	} catch (GenericException) {
		// okay
		succ = false;
	}

    /*if (succ) {
        throw std::runtime_error("an exception should have been thrown!");
    }*/

	shared_ptr<HeteroMap> info = client.get_service_info(agnos::protocol::INFO_GENERAL);
	if (info->get_as<string>("SERVICE_NAME") != "FeatureTest") {
		THROW_FORMATTED(std::runtime_error, "wrong service name: " << info->get_as<string>("SERVICE_NAME"));
	}

	info = client.get_service_info(agnos::protocol::INFO_FUNCCODES);
	for (HeteroMap::const_iterator it = info->begin(); it != info->end(); it++) {
		cout << it->first << " = " << any_cast<int32_t>(it->second) << endl;
	}

	cout << "test passed!" << endl;

	return 0;
}
