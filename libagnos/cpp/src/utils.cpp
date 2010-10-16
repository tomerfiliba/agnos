#include "utils.hpp"


namespace agnos
{
	namespace utils
	{
		Exception::Exception(const char * msg) : message(msg)
		{
		}
		Exception::Exception(const string& msg) : message(msg)
		{
		}
		Exception::~Exception() throw()
		{
		}
		const char* Exception::what() const throw ()
		{
			return message.c_str();
		}

		//////////////////////////////////////////////////////////////////////

		boost::thread::id INVALID_ID;

		Mutex::Mutex() : _real_mutex(), _tid(INVALID_ID), _lock_depth(0)
		{
		}

		Mutex::~Mutex()
		{
			// on death, just unlock the mutex as many times as necessary
			for (; _lock_depth > 0; _lock_depth -= 1) {
				_real_mutex.unlock();
			}
		}

		void Mutex::lock()
		{
			if (is_held_by_current_thread()) {
				throw MutexError("thread already owns mutex");
			}
			_real_mutex.lock();
			_tid = boost::this_thread::get_id();
			_lock_depth += 1;
		}

		void Mutex::unlock()
		{
			if (!is_held_by_current_thread()) {
				throw MutexError("thread does not own mutex");
			}
			_tid = INVALID_ID;
			_lock_depth -= 1;
			_real_mutex.unlock();
		}

		bool Mutex::is_held_by_current_thread() const
		{
			return _tid == boost::this_thread::get_id();
		}

	}
}
