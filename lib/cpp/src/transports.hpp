#ifndef AGNOS_LIB_TRANSPORTS_H_INCLUDED
#define AGNOS_LIB_TRANSPORTS_H_INCLUDED

#include <iostream>
#include <string>
#include <boost/asio.hpp>

using boost::asio::ip::tcp;

namespace agnos { namespace transports {

class ITransport
{
public:
	virtual void close() = 0;

	virtual int begin_read() = 0;
	virtual int read(char * buf, size_t size) = 0;
	virtual void end_read();

	virtual void begin_write(int seq) = 0;
	virtual void write(char * buf, size_t size) = 0;
	virtual void end_write();
	virtual void reset();
	virtual void cancel_write();
};

class BaseTransport : public ITransport
{
protected:
	std::istream& input_stream;
	std::ostream& output_stream;
	std::stringstream buffer;

public:
	BaseTransport(const std::istream& input_stream, const std::ostream& output_stream);
};

class SocketTransport : public BaseTransport
{
public:
	SocketTransport(std::string& host, int port) :
		BaseTransport(NULL, NULL)
	{
		tcp::iostream stream(host, port);
		tcp::iostream stream(host, port);
		input_stream = stream;
		output_stream = stream;
	}
};

} }


#endif
