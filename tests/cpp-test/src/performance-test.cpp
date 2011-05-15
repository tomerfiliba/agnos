#include <iostream>
#include "../bindings/FeatureTest_client_bindings.hpp"
#include "boost/date_time/posix_time/posix_time.hpp"

using namespace std;
using namespace agnos;
using namespace FeatureTest::ClientBindings;



int main(int argc, const char * argv[])
{
	//SubprocClient client("./myserver");
	if (argc != 3) {
		cerr << "usage: " << argv[0] << " <host> <port>" << endl;
	}
	SocketClient client(argv[1], argv[2]);
	client.assert_service_compatibility();

	PersonProxy NO_ONE;
	PersonProxy eve = client.Person.init("eve", NO_ONE, NO_ONE);
	PersonProxy adam = client.Person.init("adam", NO_ONE, NO_ONE);

	cout << "----------------------------------" << endl;

	// test performance
	boost::posix_time::ptime t0(boost::posix_time::microsec_clock::universal_time());
	int tmp = 0;
	const int cycles = 20;
	for (int i = 0; i < cycles; i++) {
		double res = adam->think(188, i+1);
		if (res > 2) {
			tmp = 1; // to make sure this loop is not optimized out
		}
	}
	boost::posix_time::ptime t1(boost::posix_time::microsec_clock::universal_time());
	double interval = (t1 - t0).total_microseconds() / 1000000.0;
	cout << "performing " << cycles << " cycles took " << interval << " seconds" << endl;

	return 0;
}
