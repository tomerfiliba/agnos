#include "bindings/FeatureTest_server_bindings.hpp"


using namespace agnos;
using namespace FeatureTest::ServerBindings;

/*class Person : public IPerson
{
public:
	shared_ptr<string> get_name()
	{
	}

	datetime get_date_of_birth()
	{
	}

	Address get_address()
	{
	}

	void set_address(const Address& value)
	{
	}

	shared_ptr<IPerson> get_father()
	{
	}

	shared_ptr<IPerson> get_mother()
	{
	}

	shared_ptr<IPerson> get_spouse()
	{
	}


	void marry(shared_ptr<IPerson> partner)
	{
	}

	void divorce()
	{
	}

	double think(double a, double b)
	{
	}

};

class ClassA : public IClassA
{
public:
	int32_t get_attr1()
	{
	}

	void set_attr1(int32_t value)
	{
	}

	int32_t get_attr2()
	{
	}

	void set_attr2(int32_t value)
	{
	}

	virtual int32_t method1(const string& a, bool b)
	{
	}
};

class ClassB : public IClassB
{
public:
	// attributes
	double get_attr3()
	{
	}

	void set_attr3(double value)
	{
	}

	// methods
	int32_t method2(const string& a, bool b)
	{

	}
};

class ClassC : public IClassC
{
public:
	// attributes
	shared_ptr< vector< shared_ptr< IClassA > > > get_attr4() ;

	// methods
	int32_t method3(const string& a, bool b) ;
};*/

class Handler : public IHandler
{
public:
	shared_ptr< vector< shared_ptr< IClassC > > > get_class_c()
	{
		shared_ptr< vector< shared_ptr< IClassC > > > x;
		return x;
	}

	shared_ptr<Everything> func_of_everything(int8_t a, int16_t b, int32_t c, int64_t d, double e, bool f, const datetime& g, const string& h, const string& i, shared_ptr< vector< double > > j, shared_ptr< set< int32_t > > k, shared_ptr< map< int32_t, string > > l, const Address& m, shared_ptr< IPerson > n)
	{
		return shared_ptr<Everything>(new Everything(a, b, c, d, e, f, g, h, i, j, k, l, m, n));
	}

	shared_ptr<RecordB> get_record_b()
	{
		return shared_ptr<RecordB>(new RecordB(1, 2, 3));
	}

	shared_ptr<IPerson> Person_init(const string& name, shared_ptr<IPerson> father, shared_ptr<IPerson> mother)
	{
		shared_ptr<IPerson> x;
		return x;
	}
};


int main(int argc, const char * argv[])
{
	ProcessorFactory processor_factory(shared_ptr<IHandler>(new Handler()));

	agnos::servers::CmdlineServer server(processor_factory);
	return server.main(argc, argv);
}

