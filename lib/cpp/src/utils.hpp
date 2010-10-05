#ifndef AGNOS_UTILS_HPP_INCLUDED
#define AGNOS_UTILS_HPP_INCLUDED

#include <boost/thread/thread.hpp>
#include <boost/thread/mutex.hpp>
#include "objtypes.hpp"


namespace agnos
{
	template<typename K, typename V> inline static void map_put(map<K, V>& m, const K& k, const V& v)
	{
		m.insert(typename map<K, V>::value_type(k, v));
	}

	template<typename K, typename V> inline static V * map_get(const map<K, V>& m, const K& k, bool raise = true)
	{
		typename map<K, V>::const_iterator it = m.find(k);
		if (it == m.end()) {
			if (raise) {
				throw std::out_of_range("key not found");
			}
			else {
				return NULL;
			}
		}
		return const_cast<V*>(&it->second);
	}

	namespace utils
	{
		class Exception: public std::exception
		{
		public:
			string message;

			Exception(const char * msg);
			Exception(const string& msg);
			~Exception() throw();
			virtual const char* what() const throw ();
		};

		#define DEFINE_EXCEPTION(name) \
			class name : public agnos::utils::Exception { \
			public: \
				name (const char * msg) : agnos::utils::Exception(msg) {} \
				name (const string& msg) : agnos::utils::Exception(msg) {} \
			};

		#define DEFINE_EXCEPTION2(name, base) \
			class name : public base { \
			public: \
				name (const char * msg) : base(msg) {} \
				name (const string& msg) : base(msg) {} \
			};

		DEFINE_EXCEPTION(MutexError);

		class Mutex
		{
		protected:
			boost::mutex _real_mutex;
			boost::thread::id _tid;
			int _lock_depth;

		public:
			Mutex();
			~Mutex();

			void lock();
			void unlock();
			bool is_held_by_current_thread() const;
		};

	}
}



#endif // AGNOS_UTILS_HPP_INCLUDED
