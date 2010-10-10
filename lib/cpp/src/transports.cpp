#include <iostream>
#include <sstream>
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

		//////////////////////////////////////////////////////////////////////
		// SocketTransport
		//////////////////////////////////////////////////////////////////////

		SocketTransport::SocketTransport(const string& hostname, unsigned short port) :
				wlock(), wbuf(), wseq(0),
				rlock(), rseq(0), rpos(0), rlength(0)
		{
			// ugh! the port must be a string, or it silently fails
			string portstr = convert_to_string(port);
			sockstream = shared_ptr<tcp::iostream>(new tcp::iostream(hostname, portstr.c_str()));
			if (!sockstream->good()) {
				THROW_FORMATTED(SocketTransportError, "failed connecting the socket to " << hostname << " : " << portstr);
			}
			wbuf.reserve(DEFAULT_BUFFER_SIZE);
		}

		SocketTransport::SocketTransport(const string& hostname, const string& port) :
				wlock(), wbuf(), wseq(0),
				rlock(), rseq(0), rpos(0), rlength(0)
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
				wlock(), wbuf(), wseq(0),
				rlock(), rseq(0), rpos(0), rlength(0)
		{
			_assert_good();
			wbuf.reserve(DEFAULT_BUFFER_SIZE);
		}

		string SocketTransport::to_string() const
		{
			std::stringstream ss;
			ss << "<SocketTransport " << sockstream->rdbuf()->remote_endpoint().address().to_string()
					<< ":" << sockstream->rdbuf()->remote_endpoint().port() << ">";
			return ss.str();
		}

		void SocketTransport::close()
		{
			DEBUG_LOG("");
			sockstream->rdbuf()->shutdown(tcp::socket::shutdown_both);
			sockstream->close();
			sockstream.reset();
		}

		int SocketTransport::begin_read()
		{
			if (rlock.is_held_by_current_thread()) {
				throw TransportError("begin_read is not reentrant");
			}
			rlock.lock();
			_assert_good();

			int32_t tmp;
			sockstream->read((char*)&tmp, sizeof(tmp));
			_assert_good();
			rlength = ntohl(tmp);
			DEBUG_LOG("R " << repr((char*)&tmp, sizeof(tmp)) << " rlength = " << rlength);
			sockstream->read((char*)&tmp, sizeof(tmp));
			_assert_good();
			rseq = ntohl(tmp);
			DEBUG_LOG("R " << repr((char*)&tmp, sizeof(tmp)) << " rseq = " << rseq);
			rpos = 0;
			return rseq;
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
			if (rpos + size > rlength) {
				THROW_FORMATTED(TransportError, "request to read more bytes (" << size << ") than available (" << rlength - rpos << ")");
			}
			sockstream->read(buf, size);
			size_t actually_read = sockstream->gcount();
			rpos += actually_read;
			DEBUG_LOG("R (" << size << ", " << actually_read << ") " << repr(buf, actually_read));
			return actually_read;
		}

		void SocketTransport::end_read()
		{
			DEBUG_LOG("");
			_assert_began_read();
			_assert_good();
			sockstream->ignore(rlength - rpos);
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

		void SocketTransport::reset()
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
				tmp = htonl(wbuf.size());
				DEBUG_LOG("W " << repr((const char*)&tmp, sizeof(tmp)));
				sockstream->write((const char*)&tmp, sizeof(tmp));
				tmp = htonl(wseq);
				DEBUG_LOG("W " << repr((const char*)&tmp, sizeof(tmp)));
				sockstream->write((const char*)&tmp, sizeof(tmp));
				DEBUG_LOG("W(" << wbuf.size() << ") " << repr(&wbuf[0], wbuf.size()));
				sockstream->write(&wbuf[0], wbuf.size());
				sockstream->flush();
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
				proc(proc)
		{
		}

		void ProcTransport::close()
		{
			WrappedTransport::close();
			proc.terminate(false);
		}

		shared_ptr<ProcTransport> ProcTransport::connect(const string& executable)
		{
			vector<string> args;
			args.push_back("-m");
			args.push_back("-lib");
			return connect(executable, args);
		}

		shared_ptr<ProcTransport> ProcTransport::connect(const string& executable, const vector<string>& args)
		{
			boost::process::context ctx;
			ctx.stdout_behavior = boost::process::capture_stream();
			ctx.stderr_behavior = boost::process::capture_stream();
			ctx.stdin_behavior = boost::process::capture_stream();
			ctx.environment = boost::process::self::get_environment();
			return connect(executable, args, ctx);
		}

		shared_ptr<ProcTransport> ProcTransport::connect(const string& executable, const vector<string>& args,
				const boost::process::context& ctx)
		{
			boost::process::child proc = boost::process::launch(executable, args, ctx);
			return connect(proc);
		}

		shared_ptr<ProcTransport> ProcTransport::connect(boost::process::child& proc)
		{
			char buf[200];
			boost::process::pistream& stdout = proc.get_stdout();

			memset(buf, 0, sizeof(buf));
			stdout.getline(buf, sizeof(buf));
			string magic(buf);
			if (magic.compare("AGNOS") != 0) {
				throw ProcTransportError("process either failed to start or is not an agnos server");
			}

			memset(buf, 0, sizeof(buf));
			stdout.getline(buf, sizeof(buf));
			string hostname(buf);

			memset(buf, 0, sizeof(buf));
			stdout.getline(buf, sizeof(buf));
			string port(buf);

			shared_ptr<ITransport> trns(new SocketTransport(hostname, port));
			shared_ptr<ProcTransport> proctrns(new ProcTransport(proc, trns));
			return proctrns;
		}
#endif


	}
}


