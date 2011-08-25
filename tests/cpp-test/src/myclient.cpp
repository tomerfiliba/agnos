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

	PersonProxy NO_ONE;

	cout << "(1) " << typeid(NO_ONE).name() << endl;

	PersonProxy eve = client.Person.init("eve", NO_ONE, NO_ONE);
	PersonProxy adam = client.Person.init("adam", NO_ONE, NO_ONE);

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
		adam->think(17, 0);
	} catch (GenericException) {
		// okay
		succ = false;
	}

	cout << "(10)" << endl;

    if (succ) {
        throw std::runtime_error("an exception should have been thrown!");
    }

	shared_ptr<HeteroMap> info = client.get_service_info(agnos::protocol::INFO_SERVICE);
	if (info->get_as<string>("SERVICE_NAME") != "FeatureTest") {
		THROW_FORMATTED(std::runtime_error, "wrong service name: " << info->get_as<string>("SERVICE_NAME"));
	}

	cout << "(11)" << endl;

	info = client.get_service_info(agnos::protocol::INFO_FUNCTIONS);

	cout << "(12)" << endl;

	for (HeteroMap::const_iterator it = info->begin(); it != info->end(); it++) {
		cout << it->first << " = ";
		HeteroMap v = any_cast<HeteroMap>(it->second);
		cout << " = " << v.get_as<string>("name") << endl;
	}

	cout << "(13)" << endl;

	info = client.get_service_info(agnos::protocol::INFO_META);

	for (HeteroMap::const_iterator it = info->begin(); it != info->end(); it++) {
		cout << it->first << " = " << (it->second).type().name() << endl;;
	}

	cout << "(14)" << endl;

	datetime dt = boost::posix_time::second_clock::local_time();
	bstring s1("\xff\xee\xaa\xbb");
	ustring s2("hello world");
	Address adr(NY, "Albany", "foobar drive", 1727);
	shared_ptr< vector<double> > lst(new vector<double>());
	lst->push_back(1.3);
	lst->push_back(FeatureTest::ClientBindings::pi);
	lst->push_back(4.4);
	shared_ptr< set<int32_t> > st(new set<int32_t>());
	st->insert(18);
	st->insert(19);
	st->insert(20);
	shared_ptr< map<int32_t, ustring> > mp(new map<int32_t, ustring>);
	(*mp)[34] = "foo";
	(*mp)[56] = "bar";

	shared_ptr<Everything> everything = client.func_of_everything(1, 2, 3, 4, 5.5,
				true, dt, s1, s2, lst, st, mp, adr, eve, C);

	cout << "(15)" << endl;

	if (everything->some_int32 != 3) {
        throw std::runtime_error("expected some_int to be 3");
	}

	cout << "(16)" << endl;

	shared_ptr<HeteroMap> hm1(new HeteroMap());
	hm1->put("x", "y");
	shared_ptr<HeteroMap> hm2 = client.hmap_test(1999, hm1);
	if (hm2->get_as<int>("a") != 1999) {
        throw std::runtime_error("expected 'a' to be 1999");
	}

	cout << "(17)" << endl;

	/*
	// test performance
	boost::posix_time::ptime t0(boost::posix_time::microsec_clock::local_time());
	int tmp = 0;
	const int cycles = 100;
	for (int i = 0; i < cycles; i++) {
		double res = adam->think(188, i+1);
		if (res > 2) {
			tmp = 1; // to make sure this loop is not optimized out
		}
	}
	boost::posix_time::ptime t1(boost::posix_time::microsec_clock::local_time());
	double interval = (t1 - t0).total_microseconds() / 1000000.0;
	cout << "performing " << cycles << " cycles took " << interval << " seconds" << endl;
	*/

	cout << "test passed!" << endl;

	return 0;
}
