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

		/**
		 * the abstract Transport base class
		 */
		class ITransport : public boost::noncopyable
		{
		protected:
			int compression_threshold;

			/**
			 * OVERRIDE ME
			 *
			 * returns the compression threshold. packets larger than this
			 * threshold value will be compressed. a negative value means
			 * compression is not supported on this transport.
			 */
			virtual void get_compression_threshold()
			{
				return -1;
			}

		public:
			ITransport() : compression_threshold(-1)
			{
			}

			/**
			 * closes the transport and releases all underlying operating
			 * system resources
			 */
			virtual void close() = 0;

			/**
			 * returns a string representation of this transport (usually for
			 * debugging)
			 */
			virtual string to_string() const = 0;

			/**
			 * returns whether compression has been enabled on this transport
			 */
			virtual int is_compression_enabled()
			{
				return compression_threshold >= 0;
			}

			/**
			 * attempts to enable compression on this transport. initially,
			 * compression is disabled by default, and must be explicitly
			 * enabled. note that not all transport implementations support
			 * compression, and not all versions of libagnos support compression.
			 * therefore, call this function only after checking that the other
			 * party supports compression ("COMPRESSION_SUPPORTED" is true in
			 * INFO_META)
			 *
			 * returns whether compression has been enabled.
			 */
			virtual bool enable_compression(int value)
			{
				compression_threshold = value;
				return compression_threshold >= 0;
			}

			/**
			 * disables compression on this transport
			 */
			virtual void disable_compression()
			{
				compression_threshold = -1;
			}

			//
			// read interface
			//

			/**
			 * begins a read transaction. only a single thread can have an
			 * ongoing read transaction at any point in time; other threads
			 * calling this method will block until the transaction is
			 * finalized. this method will block until enough data is received
			 * to begin the transaction. end_read() must be called to finalize
			 * the transaction.
			 * returns the sequence number of the retrieved transaction.
			 */
			virtual int32_t begin_read() = 0;

			/**
			 * reads up to `size` bytes into `buf`, and returns the actual
			 * number of bytes read.
			 * begin_read() must have been called prior to calling this.
			 */
			virtual size_t read(char * buf, size_t size) = 0;

			/**
			 * ends the ongoing read transaction (skips all unread data).
			 * begin_read() must have been called prior to calling this.
			 */
			virtual void end_read() = 0;

			//
			// write interface
			//

			/**
			 * begins a write transaction with the given sequence number. only
			 * a single thread can have an ongoing write transaction; other
			 * threads calling this method will block until the write transaction
			 * is finalized. end_write() or cancel_write() must be called to
			 * finalize the ongoing transaction.
			 */
			virtual void begin_write(int32_t seq) = 0;

			/**
			 * writes the given data of length `size` to the transport.
			 * begin_write must have been called prior to calling this.
			 */
			virtual void write(const char * buf, size_t size) = 0;

			/**
			 * discards all data written so far to the transaction, essentially
			 * restarting the transaction.
			 * begin_write must have been called prior to calling this.
			 */
			virtual void restart_write() = 0;

			/**
			 * writes all the buffered data to the underlying stream and
			 * finalizes the transaction.
			 * begin_write must have been called prior to calling this.
			 */
			virtual void end_write() = 0;

			/**
			 * cancels the ongoing write transaction. all written data is
			 * discarded and the transaction is canceled.
			 * begin_write must have been called prior to calling this.
			 */
			virtual void cancel_write() = 0;
		};

		std::ostream& operator<< (std::ostream& stream, const ITransport& trns);

		//////////////////////////////////////////////////////////////////////

		/**
		 * implements a transport that wraps an underlying transport object
		 */
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

		/**
		 * socket-backed transport implementation
		 */
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

		/**
		 * process-backed transport implementation
		 */
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


