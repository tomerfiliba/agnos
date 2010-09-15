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

		Mutex::Mutex() : _real_mutex(), _tid(INVALID_ID)
		{
		}

		Mutex::~Mutex()
		{
		}

		void Mutex::lock()
		{
			if (is_held_by_current_thread()) {
				throw MutexError("thread already owns mutex");
			}
			_real_mutex.lock();
			_tid = boost::this_thread::get_id();
		}

		void Mutex::unlock()
		{
			if (!is_held_by_current_thread()) {
				throw MutexError("thread does not own mutex");
			}
			_tid = INVALID_ID;
			_real_mutex.unlock();
		}

		bool Mutex::is_held_by_current_thread() const
		{
			return _tid == boost::this_thread::get_id();
		}

		void * get_ptr_from_any(const any& obj)
		{
			return boost::unsafe_any_cast<shared_ptr<void> >(const_cast<any*>(&obj))->get();
		}
	}
}
