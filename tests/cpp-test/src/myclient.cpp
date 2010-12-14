#include <iostream>
#include "../bindings/FeatureTest_client_bindings.hpp"

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

	cout << "(1) " << typeid(NULL_PERSON_PROXY).name() << endl;

	PersonProxy eve = client.Person.init("eve", NULL_PERSON_PROXY, NULL_PERSON_PROXY);
	PersonProxy adam = client.Person.init("adam", NULL_PERSON_PROXY, NULL_PERSON_PROXY);

	cout << "(2) " << eve << endl;
	cout << "(3) " << adam->get_name() << endl;

	eve->marry(adam);

	cout << "(4)" << endl;

	PersonProxy cain = client.Person.init("cain", adam, eve);

	cout << "(5)" << endl;

	if (cain->get_name()->compare("cain") != 0) {
		throw std::runtime_error("cain is has a wrong name");
	}

	cout << "(6)" << endl;

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

	cout << "(7)" << endl;

    if (succ) {
        throw std::runtime_error("an exception should have been thrown!");
    }

	cout << "(8)" << endl;

	double thought = adam->think(17, 3.0);
    if (thought != (17/3.0)) {
		THROW_FORMATTED(std::runtime_error, "adam thinks wrong: " << thought);
    }

	cout << "(9)" << endl;

    succ = true;
    try {
		// division by zero does not throw in c++
		adam->think(17, 0);
	} catch (GenericException) {
		// okay
		succ = false;
	}

	cout << "(10)" << endl;

    /*if (succ) {
        throw std::runtime_error("an exception should have been thrown!");
    }*/

	shared_ptr<HeteroMap> info = client.get_service_info(agnos::protocol::INFO_SERVICE);
	if (info->get_as<string>("SERVICE_NAME") != "FeatureTest") {
		THROW_FORMATTED(std::runtime_error, "wrong service name: " << info->get_as<string>("SERVICE_NAME"));
	}

	cout << "(11)" << endl;

	/*info = client.get_service_info(agnos::protocol::INFO_FUNCTIONS);

	cout << "(12)" << endl;

	for (HeteroMap::const_iterator it = info->begin(); it != info->end(); it++) {
		cout << it->first << endl;
		//" = " << (any_cast< shared_ptr<HeteroMap> >(it->second))->get_as<string>("name") << endl;
	}*/

	info = client.get_service_info(agnos::protocol::INFO_META);
	for (HeteroMap::const_iterator it = info->begin(); it != info->end(); it++) {
		cout << it->first << " = " << any_cast<int>(it->second) << endl;
	}


	cout << "(13)" << endl;

	cout << "test passed!" << endl;

	return 0;
}
