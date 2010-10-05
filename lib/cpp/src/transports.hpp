#ifndef AGNOS_TRANSPORTS_HPP_INCLUDED
#define AGNOS_TRANSPORTS_HPP_INCLUDED

#include "objtypes.hpp"
#include "utils.hpp"
#include <boost/asio.hpp>


namespace agnos
{
	namespace transports
	{
		using boost::asio::ip::tcp;

		DEFINE_EXCEPTION(TransportError);
		DEFINE_EXCEPTION2(TransportEOFError, TransportError);
		DEFINE_EXCEPTION2(SocketTransportError, TransportError);

		class ITransport : public boost::noncopyable
		{
		public:
			virtual void close() = 0;

			virtual int32_t begin_read() = 0;
			virtual size_t read(char * buf, size_t size) = 0;
			virtual void end_read() = 0;

			virtual void begin_write(int32_t seq) = 0;
			virtual void write(const char * buf, size_t size) = 0;
			virtual void reset() = 0;
			virtual void end_write() = 0;
			virtual void cancel_write() = 0;
		};

		//////////////////////////////////////////////////////////////////////

		class WrappedTransport : public ITransport
		{
		protected:
			shared_ptr<ITransport> transport;

		public:
			WrappedTransport(shared_ptr<ITransport> transport) : transport(transport)
			{
			}
			virtual void close()
			{
				transport->close();
			}
			virtual int32_t begin_read()
			{
				return transport->begin_read();
			}
			virtual size_t read(char * buf, size_t size)
			{
				return transport->read(buf, size);
			}
			virtual void end_read()
			{
				transport->end_read();
			}
			virtual void begin_write(int32_t seq)
			{
				transport->begin_write(seq);
			}
			virtual void write(const char * buf, size_t size)
			{
				transport->write(buf, size);
			}
			virtual void reset()
			{
				transport->reset();
			}
			virtual void end_write()
			{
				transport->end_write();
			}
			virtual void cancel_write()
			{
				transport->cancel_write();
			}
		};

		//////////////////////////////////////////////////////////////////////

		class DebugTransport : public ITransport
		{
		protected:
			const char * readbuf;
			size_t bufsize;
			size_t offset;

		public:
			DebugTransport(const char * readbuf, size_t size);

			virtual void close();

			virtual int32_t begin_read();
			virtual size_t read(char * buf, size_t size);
			virtual void end_read();

			virtual void begin_write(int32_t seq);
			virtual void write(const char * buf, size_t size);
			virtual void reset();
			virtual void end_write();
			virtual void cancel_write();
		};

		//////////////////////////////////////////////////////////////////////

		class SocketTransport : public ITransport
		{
		protected:
			static const size_t DEFAULT_BUFFER_SIZE = 128 * 1024;

			shared_ptr<tcp::iostream> sockstream;

			utils::Mutex wlock;
			vector<char> wbuf;
			int32_t wseq;

			utils::Mutex rlock;
			int32_t rseq;
			size_t rpos;
			size_t rlength;

			void _assert_good();
			void _assert_began_read();
			void _assert_began_write();

		public:
			SocketTransport(const string& hostname, unsigned short port);
			SocketTransport(const string& hostname, const string& port);
			SocketTransport(shared_ptr<tcp::iostream> sockstream);

			virtual void close();

			virtual int32_t begin_read();
			virtual size_t read(char * buf, size_t size);
			virtual void end_read();

			virtual void begin_write(int32_t seq);
			virtual void write(const char * buf, size_t size);
			virtual void reset();
			virtual void end_write();
			virtual void cancel_write();
		};


	}
}



#endif // AGNOS_TRANSPORTS_HPP_INCLUDED


