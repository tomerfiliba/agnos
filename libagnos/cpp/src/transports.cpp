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

#include <iostream>
#include <sstream>
#include <fstream>
#include <boost/iostreams/filtering_stream.hpp>
//#include <boost/iostreams/filtering_streambuf.hpp>
#include <boost/iostreams/device/back_inserter.hpp>
#include <boost/iostreams/copy.hpp>
#include <boost/iostreams/filter/zlib.hpp>
#include <iomanip>
#include <cstdlib>
#include <cstring>
#include "transports.hpp"


namespace agnos
{
	namespace transports
	{
		static std::string repr(const char * buf, size_t size)
		{
			std::ostringstream s;
			for (size_t i = 0; i < size; i++) {
				char ch = buf[i];
				if (ch == '\\') {
					s << "\\\\";
				}
				else if (ch >= 32 && ch <= 127) {
					s << ch;
				}
				else {
					s << "\\x" << std::hex << std::setw(2) << std::setfill('0') << (int)((unsigned char)ch);
				}
			}
			return s.str();
		}

		template <class T> inline string convert_to_string(const T& value)
		{
			// apparently this is the easiest and most portable way to convert
			// and integer to a string. who'd have thought.
			std::stringstream ss;
			ss << value;
			return ss.str();
		}

		std::ostream& operator<< (std::ostream& stream, const ITransport& trns)
		{
			stream << trns.to_string();
			return stream;
		}

		// adapted from http://lists.boost.org/boost-users/att-48158/IoStreams.cpp
		static void zlib_compress(const std::vector<char>& data, std::vector<char>& compressed)
		{
		    boost::iostreams::filtering_streambuf<boost::iostreams::output> out;
		    out.push(boost::iostreams::zlib_compressor());
		    out.push(boost::iostreams::back_inserter(compressed));
		    boost::iostreams::array_source src(&data[0], data.size());
		    boost::iostreams::copy(src, out);
		}

		/*
		static void zlib_decompress(const std::vector<char>& data, std::vector<char>& uncompressed)
		{
		    boost::iostreams::filtering_streambuf<boost::iostreams::input> in;
		    in.push(boost::iostreams::zlib_decompressor());
		    boost::iostreams::array_source src(&data[0], data.size());
		    in.push(src);
		    //?in.push(boost::make_iterator_range(data));
		    boost::iostreams::copy(in, boost::iostreams::back_inserter(uncompressed));
		}
		*/

		//////////////////////////////////////////////////////////////////////
		// SocketTransport
		//////////////////////////////////////////////////////////////////////

		SocketTransport::SocketTransport(const string& hostname, unsigned short port) :
				wlock(), wbuf(), compbuf(), wseq(0), rlock(), instream()
		{
			// ugh! the port must be a string, or it silently (!!) fails
			string portstr = convert_to_string(port);
			sockstream = shared_ptr<tcp::iostream>(new tcp::iostream(hostname, portstr.c_str()));
			if (!sockstream->good()) {
				THROW_FORMATTED(SocketTransportError, "failed connecting the socket to " << hostname << " : " << portstr);
			}
			wbuf.reserve(DEFAULT_BUFFER_SIZE);
		}

		SocketTransport::SocketTransport(const string& hostname, const string& port) :
				wlock(), wbuf(), wseq(0), rlock(), instream()
		{
			sockstream = shared_ptr<tcp::iostream>(new tcp::iostream(hostname, port.c_str()));
			if (!sockstream->good()) {
				THROW_FORMATTED(SocketTransportError, "failed connecting the socket to " << hostname << " : " << port);
			}
			wbuf.reserve(DEFAULT_BUFFER_SIZE);
		}

		inline void SocketTransport::_assert_good()
		{
			if (sockstream->eof()) {
				throw TransportEOFError("socket is closed");
			}
			if (!sockstream->good()) {
				throw SocketTransportError("sockstream is fail()ed");
			}
		}

		SocketTransport::SocketTransport(shared_ptr<tcp::iostream> sockstream) :
				sockstream(sockstream),
				wlock(), wbuf(), wseq(0), rlock(), instream()
		{
			_assert_good();
			wbuf.reserve(DEFAULT_BUFFER_SIZE);
		}

		SocketTransport::~SocketTransport()
		{
			close();
		}

		string SocketTransport::to_string() const
		{
			std::stringstream ss;
			if (sockstream) {
				ss << "<SocketTransport " << sockstream->rdbuf()->remote_endpoint().address().to_string()
					<< ":" << sockstream->rdbuf()->remote_endpoint().port() << ">";
			}
			else {
				ss << "<SocketTransport (closed)>";
			}
			return ss.str();
		}

		void SocketTransport::close()
		{
			if (sockstream.get() == NULL) {
				return;
			}
			DEBUG_LOG("SocketTransport::close");
			sockstream->rdbuf()->shutdown(tcp::socket::shutdown_both);
			sockstream->close();
			sockstream.reset();
		}

		inline int32_t SocketTransport::_read_int32()
		{
			int32_t tmp;
			sockstream->read((char*)&tmp, sizeof(tmp));
			_assert_good();
			DEBUG_LOG("R " << repr((const char*)&tmp, sizeof(tmp)));
			return ntohl(tmp);
		}

		inline void SocketTransport::_write_int32(int32_t val)
		{
			int32_t tmp = htonl(val);
			DEBUG_LOG("W " << repr((const char*)&tmp, sizeof(tmp)));
			sockstream->write((const char*)&tmp, sizeof(tmp));
			_assert_good();
		}

		template<typename T> class ZlibDecompressingStream : public BasicInputStream
		{
		protected:
			shared_ptr<T> stream;
		    boost::iostreams::filtering_stream<boost::iostreams::input> in;

		public:
			ZlibDecompressingStream(shared_ptr<T> stream) : stream(stream), in()
			{
			    in.push(boost::iostreams::zlib_decompressor());
			    in.push(*stream);
			}

			void close()
			{
				if (!stream) {
					return;
				}
				stream->close();
				stream.reset();
			}

			std::streamsize readn(char* buf, std::streamsize count)
			{
				stream->read(buf, count);
				_gcount = stream->gcount();
				return _gcount;
			}
		};

		int SocketTransport::begin_read()
		{
			if (rlock.is_held_by_current_thread()) {
				throw TransportError("begin_read is not reentrant");
			}
			rlock.lock();
			try {
				_assert_good();

				int rseq = _read_int32();
				DEBUG_LOG("rseq = " << rseq);

				int packet_length = _read_int32();
				DEBUG_LOG("packet_length = " << rlength);

				int uncompressed_length = _read_int32();
				DEBUG_LOG("uncompressed_length = " << rcomplength);

				instream = shared_ptr<BoundInputStream<tcp::iostream> >(
						new BoundInputStream<tcp::iostream>(sockstream, packet_length, true, false));

				if (uncompressed_length > 0) {
					//throw TransportError("cannot process compressed payload");

					shared_ptr<ZlibDecompressingStream<BasicInputStream> > zdc(
							new ZlibDecompressingStream<BasicInputStream>(instream));

					shared_ptr<BoundInputStream<ZlibDecompressingStream<BasicInputStream> > > bis(
							new BoundInputStream<ZlibDecompressingStream<BasicInputStream> >(
									zdc, uncompressed_length, false, true));

					instream = bis;
				}

				return rseq;
			}
			catch (std::exception &ex) {
				rlock.unlock();
				throw;
			}
		}

		inline void SocketTransport::_assert_began_read()
		{
			if (!rlock.is_held_by_current_thread()) {
				throw TransportError("thread must first call begin_read");
			}
		}

		size_t SocketTransport::read(char * buf, size_t size)
		{
			_assert_began_read();
			_assert_good();
			size_t actually_read = instream->readn(buf, size);
			DEBUG_LOG("R (" << size << ", " << actually_read << ") " << repr(buf, actually_read));
			return actually_read;
		}

		void SocketTransport::end_read()
		{
			DEBUG_LOG("");
			_assert_began_read();
			instream->close();
			instream.reset();
			rlock.unlock();
		}

		void SocketTransport::begin_write(int32_t seq)
		{
			DEBUG_LOG("seq = " << seq);
			if (wlock.is_held_by_current_thread()) {
				throw TransportError("begin_write is not reentrant");
			}
			wlock.lock();
			_assert_good();
			wseq = seq;
			wbuf.clear();
			wbuf.reserve(DEFAULT_BUFFER_SIZE);
		}

		inline void SocketTransport::_assert_began_write()
		{
			if (!wlock.is_held_by_current_thread()) {
				throw TransportError("thread must first call begin_write");
			}
		}

		void SocketTransport::write(const char * buf, size_t size)
		{
			DEBUG_LOG("W (" << size << ") " << repr(buf, size));
			_assert_began_write();
			_assert_good();
			wbuf.insert(wbuf.end(), buf, buf + size);
		}

		void SocketTransport::restart_write()
		{
			DEBUG_LOG("");
			_assert_began_write();
			wbuf.clear();
			wbuf.reserve(DEFAULT_BUFFER_SIZE);
		}

		void SocketTransport::end_write()
		{
			int32_t tmp;
			_assert_began_write();
			_assert_good();

			if (wbuf.size() > 0) {
				if (wbuf.size() > compression_threshold) {
					DEBUG_LOG("COMPRESSING!");
					compbuf.clear();
					compbuf.reserve(wbuf.size());
					zlib_compress(wbuf, compbuf);

					_write_int32(wseq);            // seq
					_write_int32(compbuf.size());  // packet length
					_write_int32(wbuf.size());     // 0 means uncompressed

					DEBUG_LOG("W(" << compbuf.size() << ") " << repr(&compbuf[0], compbuf.size()));
					sockstream->write(&compbuf[0], compbuf.size());
					compbuf.clear();
				}
				else {
					_write_int32(wseq);            // seq
					_write_int32(wbuf.size());     // packet length
					_write_int32(0);               // 0 means uncompressed

					DEBUG_LOG("W(" << wbuf.size() << ") " << repr(&wbuf[0], wbuf.size()));
					sockstream->write(&wbuf[0], wbuf.size());
				}
				sockstream->flush();
				_assert_good();
				wbuf.clear();
				wbuf.reserve(DEFAULT_BUFFER_SIZE);
			}
			wlock.unlock();
		}

		void SocketTransport::cancel_write()
		{
			DEBUG_LOG("");
			_assert_began_write();
			wbuf.clear();
			wbuf.reserve(DEFAULT_BUFFER_SIZE);
			wlock.unlock();
		}

		//////////////////////////////////////////////////////////////////////
		// ProcTransport
		//////////////////////////////////////////////////////////////////////


#ifdef BOOST_PROCESS_SUPPORTED
		ProcTransport::ProcTransport(boost::process::child& proc, shared_ptr<ITransport> transport) :
				WrappedTransport(transport),
				proc(proc),
				_closed(false)
		{
		}

		ProcTransport::~ProcTransport()
		{
			close();
		}

		void ProcTransport::close()
		{
			if (_closed) {
				return;
			}
			DEBUG_LOG("ProcTransport::close");
			WrappedTransport::close();
			proc.terminate(false);
			_closed = true;
		}

		shared_ptr<ProcTransport> ProcTransport::connect(const string& executable)
		{
			vector<string> args;
			args.push_back(executable);
			args.push_back("-m");
			args.push_back("lib");
			return connect(executable, args);
		}

		shared_ptr<ProcTransport> ProcTransport::connect(const string& executable, const vector<string>& args)
		{
			boost::process::context ctx;
			ctx.stdin_behavior = boost::process::capture_stream();
			ctx.stdout_behavior = boost::process::capture_stream();
			ctx.stderr_behavior = boost::process::inherit_stream();
			ctx.environment = boost::process::self::get_environment();
			return connect(executable, args, ctx);
		}

		shared_ptr<ProcTransport> ProcTransport::connect(const string& executable, const vector<string>& args,
				const boost::process::context& ctx)
		{
			boost::process::child proc = boost::process::launch(executable, args, ctx);
			string sargs;
			for (int i = 0; i < args.size(); i++) {
				sargs += args[i] + " ";
			}
			DEBUG_LOG("launched process " << executable << ", args = " << sargs);
			return connect(proc);
		}

		shared_ptr<ProcTransport> ProcTransport::connect(boost::process::child& proc)
		{
			char buf[200];
			boost::process::pistream& stdout = proc.get_stdout();

			memset(buf, 0, sizeof(buf));
			stdout.getline(buf, sizeof(buf));
			string magic(buf);
			DEBUG_LOG("magic = " << magic);

			if (magic.compare("AGNOS") != 0) {
				throw ProcTransportError("process either failed to start or is not an agnos server");
			}

			memset(buf, 0, sizeof(buf));
			stdout.getline(buf, sizeof(buf));
			string hostname(buf);
			DEBUG_LOG("hostname = " << hostname);

			memset(buf, 0, sizeof(buf));
			stdout.getline(buf, sizeof(buf));
			string port(buf);
			DEBUG_LOG("port = " << port);

			shared_ptr<ITransport> trns(new SocketTransport(hostname, port));
			shared_ptr<ProcTransport> proctrns(new ProcTransport(proc, trns));
			return proctrns;
		}
#endif


	}
}


