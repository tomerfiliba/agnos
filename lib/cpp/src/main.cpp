#include <iostream>
#include "transports.hpp"
#include "packers.hpp"


using std::cout;
using std::cin;
using std::endl;
using namespace agnos;

class A
{
	class B
	{
		void bar();
	};

	void foo();
};

void A::foo()
{

}

void A::B::bar()
{

}




int main(int argc, const char * argv[])
{
	char bytes[] = "\x00\x00\x00\x02" "\x00\x00\x00\x0b" "hello world" "\x00\x00\x00\x03" "foo";
	transports::DebugTransport trns(bytes, sizeof(bytes));


#ifdef _MSC_VER
	char __x[10];
	cin.getline(__x, sizeof(__x));
#endif
	return 0;
}

