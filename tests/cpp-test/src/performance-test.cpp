#include <iostream>
#include <boost/asio.hpp>
#include <boost/array.hpp>

using boost::asio::ip::tcp;


int main()
{
	boost::asio::io_service the_io_service;
	//char buf[100];

	tcp::acceptor acceptor(the_io_service);
	tcp::endpoint ep(boost::asio::ip::address::from_string("127.0.0.1"), 17788);

	acceptor.open(ep.protocol());
	acceptor.set_option(tcp::acceptor::reuse_address(true));
	acceptor.bind(ep);
	acceptor.listen(1);

	std::cout << "accepting..." << std::endl;

	//tcp::socket mysocket(the_io_service);
	//acceptor.accept(mysocket);
	tcp::iostream sockstream;
	acceptor.accept(*(sockstream.rdbuf()));

	std::cout << "got client" << std::endl;

	char buf[100];
	boost::system::error_code myerror;

	sockstream.rdbuf()->read_some(boost::asio::buffer(buf, sizeof(buf)), myerror);
	std::streamsize count = sockstream.gcount();

	std::size_t count = mysocket.read_some(boost::asio::buffer(buf, sizeof(buf)), myerror);
	if (myerror == boost::asio::error::eof) {
		// Connection closed cleanly by peer.
	}
	else if (myerror) {
		throw boost::system::system_error(myerror); // Some other error.
	}

	std::cout << "got " << count << " bytes" << std::endl;

	//sockstream.rdbuf()->shutdown(tcp::socket::shutdown_both);
	//sockstream.close();
	//mysocket.shutdown(tcp::socket::shutdown_both);
	//mysocket.close();
	acceptor.close();

	return 0;
}

