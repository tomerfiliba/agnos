#include <iostream>
#include <sstream>
#include <iomanip>
#include "string.h"
#include "transports.hpp"



namespace agnos
{
	namespace transports
	{
		//////////////////////////////////////////////////////////////////////
		// DebugTransport
		//////////////////////////////////////////////////////////////////////

		DebugTransport::DebugTransport(const char * readbuf, size_t size) :
			readbuf(readbuf), bufsize(size), offset(0)
		{
		}

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

		size_t DebugTransport::read(char * buf, size_t size)
		{
			if (offset >= bufsize) {
				std::cout << "R(" << size << "): EOF";
				return 0;
			}
			size_t count = (size <= bufsize - offset) ? size : bufsize - offset;
			memcpy(buf, readbuf + offset, count);
			offset += count;
			std::cout << "R(" << size << "->" << count << "): " << repr(buf, size) << std::endl;
			return count;
		}

		void DebugTransport::write(const char * buf, size_t size)
		{
			std::cout << "W(" << size << "): " << repr(buf, size) << std::endl;
		}

		void DebugTransport::close()
		{
			std::cout << ".close" << std::endl;
		}
		int32_t DebugTransport::begin_read()
		{
			std::cout << ".begin_read" << std::endl;
			return -1;
		}
		void DebugTransport::end_read()
		{
			std::cout << ".end_read" << std::endl;
		}
		void DebugTransport::begin_write(int32_t seq)
		{
			std::cout << ".begin_write " << seq << std::endl;
		}
		void DebugTransport::reset()
		{
			std::cout << ".reset" << std::endl;
		}
		void DebugTransport::end_write()
		{
			std::cout << ".end_write" << std::endl;
		}
		void DebugTransport::cancel_write()
		{
			std::cout << ".cancel_write" << std::endl;
		}

		//////////////////////////////////////////////////////////////////////
		// SocketTransport
		//////////////////////////////////////////////////////////////////////

		SocketTransport::SocketTransport(const string& hostname, unsigned short port) :
				wlock(), wbuf(), wseq(0),
				rlock(), rseq(0), rpos(0), rlength(0)
		{
			sockstream = shared_ptr<tcp::iostream>(new tcp::iostream(hostname, port));
			wbuf.reserve(DEFAULT_BUFFER_SIZE);
		}

		SocketTransport::SocketTransport(shared_ptr<tcp::iostream> sockstream) :
				sockstream(sockstream),
				wlock(), wbuf(), wseq(0),
				rlock(), rseq(0), rpos(0), rlength(0)
		{
			wbuf.reserve(DEFAULT_BUFFER_SIZE);
		}

		void SocketTransport::close()
		{
#ifdef AGNOS_DEBUG
			std::cout << ":: close()" << std::endl;
#endif

			sockstream->rdbuf()->shutdown(tcp::socket::shutdown_both);
			sockstream->close();
		}

		int SocketTransport::begin_read()
		{
#ifdef AGNOS_DEBUG
			std::cout << ":: begin_read()" << std::endl;;
#endif
			if (rlock.is_held_by_current_thread()) {
				throw TransportError("begin_read is not reentrant");
			}
			rlock.lock();

			int32_t tmp;
			sockstream->read((char*)&tmp, sizeof(tmp));
			rlength = ntohl(tmp);
			sockstream->read((char*)&tmp, sizeof(tmp));
			rseq = ntohl(tmp);
			rpos = 0;
#ifdef AGNOS_DEBUG
			std::cout << "length = " << rlength << ", seq = " << rseq << std::endl;
#endif
			return rseq;
		}

		static inline void _assert_began_read(utils::Mutex& mutex)
		{
			if (!mutex.is_held_by_current_thread()) {
				throw TransportError("thread must first call begin_read");
			}
		}

		size_t SocketTransport::read(char * buf, size_t size)
		{
#ifdef AGNOS_DEBUG
			std::cout << ":: read(" << size << ")" << std::endl;
#endif
			_assert_began_read(rlock);
			if (rpos + size > rlength) {
				throw TransportError("request to read more than available");
			}
			sockstream->read(buf, size);
			size_t actually_read = sockstream->gcount();
			rpos += actually_read;
#ifdef AGNOS_DEBUG
			std::cout << "data(" << actually_read << ") : " << repr(buf, actually_read) << std::endl;
#endif
			return actually_read;
		}

		void SocketTransport::end_read()
		{
#ifdef AGNOS_DEBUG
			std::cout << ":: end_read()" << std::endl;
#endif
			_assert_began_read(rlock);
			sockstream->ignore(rlength - rpos);
			rlock.unlock();
		}

		void SocketTransport::begin_write(int32_t seq)
		{
#ifdef AGNOS_DEBUG
			std::cout << ":: begin_write(" << seq << ")" << std::endl;
#endif
			if (wlock.is_held_by_current_thread()) {
				throw TransportError("begin_write is not reentrant");
			}
			wlock.lock();
			wseq = seq;
			wbuf.clear();
			wbuf.reserve(DEFAULT_BUFFER_SIZE);
		}

		static inline void _assert_began_write(utils::Mutex& mutex)
		{
			if (!mutex.is_held_by_current_thread()) {
				throw TransportError("thread must first call begin_write");
			}
		}

		void SocketTransport::write(const char * buf, size_t size)
		{
#ifdef AGNOS_DEBUG
			std::cout << ":: write(" << size << ") : " <<repr(buf, size) << std::endl;
#endif
			_assert_began_write(wlock);
			wbuf.insert(wbuf.end(), buf, buf + size);
		}

		void SocketTransport::reset()
		{
#ifdef AGNOS_DEBUG
			std::cout << ":: reset()" << std::endl;
#endif
			_assert_began_write(wlock);
			wbuf.clear();
			wbuf.reserve(DEFAULT_BUFFER_SIZE);
		}

		void SocketTransport::end_write()
		{
#ifdef AGNOS_DEBUG
			std::cout << ":: end_write()" << std::endl;
#endif
			int32_t tmp;
			_assert_began_write(wlock);
			if (wbuf.size() > 0) {
				tmp = htonl(wbuf.size());
				sockstream->write((const char*)&tmp, sizeof(tmp));
				tmp = htonl(wseq);
				sockstream->write((const char*)&tmp, sizeof(tmp));

				sockstream->write(&wbuf[0], wbuf.size());
				sockstream->flush();
				wbuf.clear();
				wbuf.reserve(DEFAULT_BUFFER_SIZE);
			}
			wlock.unlock();
		}

		void SocketTransport::cancel_write()
		{
#ifdef AGNOS_DEBUG
			std::cout << ":: cancel_write()" << std::endl;
#endif
			_assert_began_write(wlock);
			wbuf.clear();
			wbuf.reserve(DEFAULT_BUFFER_SIZE);
			wlock.unlock();
		}


	}
}


