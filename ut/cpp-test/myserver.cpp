#include "bindings/simple_server_bindings.hpp"

using namespace agnos;
using namespace simple::ServerBindings;


class Person : public IPerson
{
protected:
	shared_ptr<string> _full_name;
	datetime _dob;

public:
	Person(const string& full_name, datetime dob) :
		_full_name(new string(full_name)),
		_dob(dob)
	{
	}

	shared_ptr<string> get_full_name()
	{
		return _full_name;
	}

	datetime get_dob()
	{
		return _dob;
	}

	shared_ptr<IPerson> give_birth(const string& full_name)
	{
		shared_ptr<IPerson> child(new Person(full_name, boost::posix_time::second_clock::universal_time()));
		return child;
	}

};


class Handler : public IHandler
{
public:
	int32_t add(int a, int b)
	{
		return a + b;
	}

	shared_ptr<Address> get_address(const string& country, const string& city, const string& street, int32_t num)
	{
		return shared_ptr<Address>(new Address(country, city, street, num + 1));
	}

	shared_ptr<Address> modify_address(const Address& addr)
	{
		return shared_ptr<Address>(new Address(addr.country, addr.city, addr.street, addr.num * 2));
	}

	shared_ptr<IPerson> get_father()
	{
		shared_ptr<IPerson> father(new Person("moshe buzaglo", boost::posix_time::from_iso_string("19850407T112233")));
		return father;
	}

};


int main(int argc, const char * argv[])
{
	ProcessorFactory processor_factory(shared_ptr<IHandler>(new Handler()));

	agnos::servers::CmdlineServer server(processor_factory);
	return server.main(argc, argv);
}

