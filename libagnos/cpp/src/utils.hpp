//////////////////////////////////////////////////////////////////////////////
// Part of the Agnos RPC Framework
//    http://agnos.sourceforge.net
//
// Copyright 2010, International Business Machines Corp.
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

#ifndef AGNOS_UTILS_HPP_INCLUDED
#define AGNOS_UTILS_HPP_INCLUDED

#include <sstream>
#include <boost/thread/thread.hpp>
#include <boost/thread/mutex.hpp>
#include "objtypes.hpp"

#ifdef AGNOS_DEBUG
#	include <unistd.h>
#	define DEBUG_LOG(text) \
	std::cerr << "[" << getpid() << ":" << __FUNCTION__ << "(" << __LINE__ << ")" << "] " << text << std::endl;
#else
#define DEBUG_LOG(text)
#endif

#define THROW_FORMATTED(cls, text) { std::stringstream _ss; _ss << text; throw cls(_ss.str()); }

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
				THROW_FORMATTED(std::out_of_range, "key not found: " << k << ", map type = " << typeid(m).name());
			}
			else {
				return NULL;
			}
		}
		return const_cast<V*>(&it->second);
	}

	template<typename K, typename V> inline static bool map_contains(map<K, V>& m, const K& k)
	{
		typename map<K, V>::const_iterator it = m.find(k);
		return it != m.end();
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
