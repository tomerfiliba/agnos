#include <cstdlib>
#include <boost/enable_shared_from_this.hpp>
#include "../bindings/FeatureTest_server_bindings.hpp"

using namespace agnos;
using namespace FeatureTest::ServerBindings;


//
// classes
//
class ClassA : public IClassA
{
	public:
	int32_t get_attr1()
	{
		return 17;
	}
	void set_attr1(int32_t value)
	{
	}

	int32_t get_attr2()
	{
		return 199;
	}
	void set_attr2(int32_t value)
	{
	}

	int32_t method1(const string& a, bool b)
	{
		int v = b ? 7 : 3;
		return atoi(a.c_str()) + v;
	}

};

class ClassB : public IClassB
{
	protected:
	int32_t _attr1;
	double _attr3;

	public:
	ClassB()
	{
		_attr1 = 17;
		_attr3 = 17.777;
	}

	int32_t get_attr1()
	{
		return _attr1;
	}
	void set_attr1(int32_t value)
	{
		_attr1 = value;
	}

	int32_t get_attr2()
	{
		return 211;
	}
	void set_attr2(int32_t value)
	{
	}

	double get_attr3()
	{
		return _attr3;
	}
	void set_attr3(double value)
	{
		_attr3 = value * 2;
	}

	int32_t method1(const string& a, bool b)
	{
		int v = b ? 7 : 3;
		return atoi(a.c_str()) + v;
	}

	int32_t method2(const string& a, bool b)
	{
		int v = b ? 99 : 33;
		return atoi(a.c_str()) + v;
	}

};

class ClassC : public IClassC
{
	protected:
	int32_t _attr1;
	double _attr3;
	shared_ptr< vector< shared_ptr<IClassA> > > _attr4;

	public:
	ClassC(int32_t attr1, int32_t attr2, double attr3, shared_ptr< vector< shared_ptr<IClassA> > > attr4) :
		_attr1(attr1),
		_attr3(attr3),
		_attr4(attr4)
	{
	}

	int32_t get_attr1()
	{
		return _attr1;
	}
	void set_attr1(int32_t value)
	{
		_attr1 = value;
	}

	int32_t get_attr2()
	{
		return 399;
	}
	void set_attr2(int32_t value)
	{
	}

	double get_attr3()
	{
		return _attr3;
	}
	void set_attr3(double value)
	{
		_attr3 = value * 2;
	}

	shared_ptr< vector< shared_ptr<IClassA> > > get_attr4()
	{
		return _attr4;
	}

	int32_t method1(const string& a, bool b)
	{
		int v = b ? 7 : 3;
		return atoi(a.c_str()) + v;
	}

	int32_t method2(const string& a, bool b)
	{
		int v = b ? 99 : 33;
		return atoi(a.c_str()) + v;
	}

	int32_t method3(const string& a, bool b)
	{
		int v = b ? 22 : -22;
		return atoi(a.c_str()) + v;
	}

};

class Person : public IPerson, public boost::enable_shared_from_this<Person>
{
	protected:
	shared_ptr<string> _name;
	datetime _date_of_birth;
	shared_ptr<Address> _address;
	shared_ptr<IPerson> _father;
	shared_ptr<IPerson> _mother;
	shared_ptr<IPerson> _spouse;

	public:
	Person(const string& name, shared_ptr<IPerson> father, shared_ptr<IPerson> mother) :
		_name(shared_ptr<string>(new string(name))),
		_father(father),
		_mother(mother),
		_spouse(),
		_address(new Address(TX, "nashville", "woldorf", 1772)),
		_date_of_birth(boost::posix_time::second_clock::universal_time())
	{
	}

	shared_ptr<string> get_name()
	{
		return _name;
	}

	datetime get_date_of_birth()
	{
		return _date_of_birth;
	}

	shared_ptr<Address> get_address()
	{
		return _address;
	}
	void set_address(const Address& value)
	{
		_address.reset(new Address(value));
	}

	shared_ptr<IPerson> get_father()
	{
		return _father;
	}

	shared_ptr<IPerson> get_mother()
	{
		return _mother;
	}

	shared_ptr<IPerson> get_spouse()
	{
		return _spouse;
	}

	void marry(shared_ptr<IPerson> partner)
	{
		if (_spouse) {
			throw MartialStatusError("already married", shared_from_this());
		}
		if (partner->get_spouse()) {
			throw MartialStatusError("already married", partner);
		}
		if ((_mother && _mother == partner->get_mother())
				|| (_father && _father == partner->get_father())) {
			throw MartialStatusError("siblings cannot marry", partner);
		}
		_spouse = partner;
		boost::dynamic_pointer_cast<Person>(partner)->_spouse = shared_from_this();
	}

	void divorce()
	{
		if (!_spouse) {
			throw MartialStatusError("does not have a spouse", shared_from_this());
		}
		boost::dynamic_pointer_cast<Person>(_spouse)->_spouse.reset();
		_spouse.reset();
	}

	double think(double a, double b)
	{
		if (b == 0) {
			throw std::runtime_error("division by zero!");
		}
		return a / b;
	}

};

//
// handler
//
class Handler : public IHandler
{
	public:
	shared_ptr< vector< shared_ptr<IClassC> > > get_class_c()
	{
		shared_ptr<vector<shared_ptr<IClassC> > > arr(new vector<shared_ptr<IClassC> >());

		shared_ptr<vector<shared_ptr<IClassA> > > x1(new vector<shared_ptr<IClassA> >());
		x1->push_back(shared_ptr<IClassA>(new ClassA()));
		x1->push_back(shared_ptr<IClassA>(new ClassA()));

		shared_ptr<vector<shared_ptr<IClassA> > > x2(new vector<shared_ptr<IClassA> >());
		x1->push_back(shared_ptr<IClassA>(new ClassA()));

		arr->push_back(shared_ptr<IClassC>(new ClassC(4, 5, 6.0, x1)));
		arr->push_back(shared_ptr<IClassC>(new ClassC(33, 12, 76.2, x2)));

		return arr;
	}

	shared_ptr<Everything> func_of_everything(int8_t a, int16_t b, int32_t c, int64_t d, double e,
			bool f, const datetime& g, const string& h, const string& i, shared_ptr< vector< double > > j,
			shared_ptr< set< int32_t > > k, shared_ptr< map< int32_t, string > > l,
			const Address& m, shared_ptr<IPerson> n, MyEnum o)
	{
		return shared_ptr<Everything>(new Everything(a, b, c, d, e, f, g, h, i, j, k, l, m, n));
	}

	shared_ptr<RecordB> get_record_b()
	{
		return shared_ptr<RecordB>(new RecordB(17, 18, 19));
	}

	shared_ptr<IPerson> Person_init(const string& name, shared_ptr<IPerson> father, shared_ptr<IPerson> mother)
	{
		return shared_ptr<Person>(new Person(name, father, mother));
	}

	shared_ptr<HeteroMap> hmap_test(int32_t a, shared_ptr<HeteroMap> b)
	{
		shared_ptr<HeteroMap> hm(new HeteroMap());
		hm->put("a", a);
		hm->put("b", 18);
		return hm;
	}


};

//
// main
//
int main(int argc, const char * argv[])
{
	ProcessorFactory processor_factory(shared_ptr<IHandler>(new Handler()));

	agnos::servers::CmdlineServer server(processor_factory);
	return server.main(argc, argv);
}
