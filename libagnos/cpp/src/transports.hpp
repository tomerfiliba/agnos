//////////////////////////////////////////////////////////////////////////////
// Part of the Agnos RPC Framework
//    http://agnos.sourceforge.net
//
// Copyright 2011, International Business Machines Corp.
//                 Author: Tomer Filiba (tomerf@il.ibm.com)
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//    http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.
//////////////////////////////////////////////////////////////////////////////

#ifndef AGNOS_TRANSPORTS_HPP_INCLUDED
#define AGNOS_TRANSPORTS_HPP_INCLUDED

#include "objtypes.hpp"
#include "utils.hpp"
#include <boost/asio.hpp>

#ifdef BOOST_PROCESS_SUPPORTED
/*
 * fetch BOOST::Process from http://www.highscore.de/boost/process/ and
 * define BOOST_PROCESS_SUPPORTED
 *
 * it's not yet officially included in boost itself, so it has to be
 * downloaded manually and placed along with your boost includes
 * e.g., /usr/include/boost/process.hpp
 *
 * supports Windows and POSIX
 */
#include <boost/process.hpp>
#endif

//#ifdef BOOST_HTTP_SUPPORTED
//#include <boost/network/protocol/http.hpp>
//#endif

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
		protected:
			int compression_threshold;

		public:
			ITransport() : compression_threshold(-1)
			{
			}

			virtual void close() = 0;

			virtual int get_compression_threshold()
			{
				return compression_threshold;
			}
			virtual void set_compression_threshold(int value)
			{
				compression_threshold = value;
			}
			virtual void disable_compression()
			{
				compression_threshold = -1;
			}

			virtual int32_t begin_read() = 0;
			virtual size_t read(char * buf, size_t size) = 0;
			virtual void end_read() = 0;

			virtual void begin_write(int32_t seq) = 0;
			virtual void write(const char * buf, size_t size) = 0;
			virtual void reset() = 0;
			virtual void end_write() = 0;
			virtual void cancel_write() = 0;

			virtual string to_string() const = 0;
		};

		std::ostream& operator<< (std::ostream& stream, const ITransport& trns);

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
			virtual string to_string() const
			{
				return transport->to_string();
			}
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
			size_t rcomplength;

			void _assert_good();
			void _assert_began_read();
			void _assert_began_write();

		public:
			SocketTransport(const string& hostname, unsigned short port);
			SocketTransport(const string& hostname, const string& port);
			SocketTransport(shared_ptr<tcp::iostream> sockstream);

			~SocketTransport();

			void close();

			int32_t begin_read();
			size_t read(char * buf, size_t size);
			void end_read();

			void begin_write(int32_t seq);
			void write(const char * buf, size_t size);
			void reset();
			void end_write();
			void cancel_write();

			string to_string() const;
		};

#ifdef BOOST_PROCESS_SUPPORTED
		DEFINE_EXCEPTION(ProcTransportError)

		class ProcTransport : public WrappedTransport
		{
		protected:
			boost::process::child proc;
			bool _closed;

		public:
			ProcTransport(boost::process::child& proc, shared_ptr<ITransport> transport);
			~ProcTransport();

			void close();

			static shared_ptr<ProcTransport> connect(const string& executable);
			static shared_ptr<ProcTransport> connect(const string& executable, const vector<string>& args);
			static shared_ptr<ProcTransport> connect(const string& executable, const vector<string>& args,
					const boost::process::context& ctx);
			static shared_ptr<ProcTransport> connect(boost::process::child& proc);
		};
#endif

#ifdef BOOST_HTTP_SUPPORTED
		class HttpTransport : public ITransport
		{
		public:
			HttpTransport(const string& url)
			{
			}
		};
#endif


	}
}



#endif // AGNOS_TRANSPORTS_HPP_INCLUDED


