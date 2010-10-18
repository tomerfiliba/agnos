//////////////////////////////////////////////////////////////////////////////
// Part of the Agnos RPC Framework
//    http://agnos.sourceforge.net
//
// Copyright 2010, Tomer Filiba (tomerf@il.ibm.com; tomerfiliba@gmail.com)
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

#ifndef AGNOS_HETEROMAP_HPP_INCLUDED
#define AGNOS_HETEROMAP_HPP_INCLUDED

#include <sstream>
#include "objtypes.hpp"
#include "packers.hpp"
#include "utils.hpp"


namespace agnos
{
	using packers::IPacker;

	namespace packers
	{
		class HeteroMapPacker;
	}

	DEFINE_EXCEPTION(HeteroMapError);

	class HeteroMap
	{
	public:
		/*
		 * for some reason, 'const char *' prefers to coerce itself to an int,
		 * rather than a std::string, when given an option, so we'll have to
		 * specialize these cases
		 */

		typedef variant<string, bool, int32_t, int64_t, double, datetime> key_type;
		typedef any mapped_type;

	protected:
		typedef map<key_type, any> map_type;

		struct PackerInfo
		{
			const IPacker& keypacker;
			const IPacker& valpacker;
			PackerInfo(const IPacker& kp, const IPacker& vp) : keypacker(kp), valpacker(vp)
			{
			}
		};

		typedef map<key_type, PackerInfo> packers_info_type;

		map_type data;
		mutable packers_info_type packers_info;

		friend class packers::HeteroMapPacker;

	public:
		typedef map_type::const_iterator const_iterator;
		typedef map_type::iterator iterator;
		typedef map_type::size_type size_type;
		typedef map_type::value_type value_type;

		HeteroMap();
		HeteroMap(const HeteroMap& other);
		HeteroMap& operator= (const HeteroMap& rhs);

		inline void clear()
		{
			data.clear();
		}
		inline bool empty() const
		{
			return data.empty();
		}
		inline size_type size() const
		{
			return data.size();
		}
		inline size_type erase(const char * key)
		{
			return erase(string(key));
		}
		inline size_type erase(const key_type& key)
		{
			return data.erase(key);
		}
		inline iterator begin()
		{
			return data.begin();
		}
		inline const_iterator begin() const
		{
			return data.begin();
		}
		inline iterator end()
		{
			return data.end();
		}
		inline const_iterator end() const
		{
			return data.end();
		}
		inline iterator find(const char* key)
		{
			return find(string(key));
		}
		inline iterator find(const key_type& key)
		{
			return data.find(key);
		}
		inline const_iterator find(const char* key) const
		{
			return find(string(key));
		}
		inline const_iterator find(const key_type& key) const
		{
			return data.find(key);
		}
		inline bool contains(const char* key) const
		{
			return contains(string(key));
		}
		inline bool contains(const key_type& key) const
		{
			return find(key) != end();
		}

		void put(const key_type& key, const IPacker& keypacker, const any& value, const IPacker& valpacker);

		inline void put(const char * key, const IPacker& keypacker, const any& value, const IPacker& valpacker)
		{
			put(string(key), keypacker, value, valpacker);
		}

		inline void put(int32_t key, const char * value)
		{
			put(key, string(value));
		}
		inline void put(int32_t key, const string& value)
		{
			put(key, packers::int32_packer, value, packers::string_packer);
		}
		inline void put(int32_t key, int32_t value)
		{
			put(key, packers::int32_packer, value, packers::int32_packer);
		}
		inline void put(int32_t key, int64_t value)
		{
			put(key, packers::int32_packer, value, packers::int64_packer);
		}
		inline void put(int32_t key, double value)
		{
			put(key, packers::int32_packer, value, packers::float_packer);
		}
		inline void put(int32_t key, datetime value)
		{
			put(key, packers::int32_packer, value, packers::date_packer);
		}
		inline void put(int32_t key, bool value)
		{
			put(key, packers::int32_packer, value, packers::bool_packer);
		}

		inline void put(int64_t key, const char * value)
		{
			put(key, string(value));
		}
		inline void put(int64_t key, int32_t value)
		{
			put(key, packers::int64_packer, value, packers::int32_packer);
		}
		inline void put(int64_t key, int64_t value)
		{
			put(key, packers::int64_packer, value, packers::int64_packer);
		}
		inline void put(int64_t key, const string& value)
		{
			put(key, packers::int64_packer, value, packers::string_packer);
		}
		inline void put(int64_t key, double value)
		{
			put(key, packers::int64_packer, value, packers::float_packer);
		}
		inline void put(int64_t key, datetime value)
		{
			put(key, packers::int64_packer, value, packers::date_packer);
		}
		inline void put(int64_t key, bool value)
		{
			put(key, packers::int64_packer, value, packers::bool_packer);
		}

		inline void put(double key, const char * value)
		{
			put(key, string(value));
		}
		inline void put(double key, const string& value)
		{
			put(key, packers::float_packer, value, packers::string_packer);
		}
		inline void put(double key, int32_t value)
		{
			put(key, packers::float_packer, value, packers::int32_packer);
		}
		inline void put(double key, int64_t value)
		{
			put(key, packers::float_packer, value, packers::int64_packer);
		}
		inline void put(double key, double value)
		{
			put(key, packers::float_packer, value, packers::float_packer);
		}
		inline void put(double key, datetime value)
		{
			put(key, packers::float_packer, value, packers::date_packer);
		}
		inline void put(double key, bool value)
		{
			put(key, packers::float_packer, value, packers::bool_packer);
		}

		inline void put(const string& key, const char * value)
		{
			put(key, string(value));
		}
		inline void put(const string& key, int32_t value)
		{
			put(key, packers::string_packer, value, packers::int32_packer);
		}
		inline void put(const string& key, int64_t value)
		{
			put(key, packers::string_packer, value, packers::int64_packer);
		}
		inline void put(const string& key, const string& value)
		{
			put(key, packers::string_packer, value, packers::string_packer);
		}
		inline void put(const string& key, double value)
		{
			put(key, packers::string_packer, value, packers::float_packer);
		}
		inline void put(const string& key, datetime value)
		{
			put(key, packers::string_packer, value, packers::date_packer);
		}
		inline void put(const string& key, bool value)
		{
			put(key, packers::string_packer, value, packers::bool_packer);
		}

		inline void put(const char* key, const char * value)
		{
			put(string(key), string(value));
		}
		inline void put(const char* key, int32_t value)
		{
			put(string(key), value);
		}
		inline void put(const char* key, int64_t value)
		{
			put(string(key), value);
		}
		inline void put(const char* key, const string& value)
		{
			put(string(key), value);
		}
		inline void put(const char* key, double value)
		{
			put(string(key), value);
		}
		inline void put(const char* key, datetime value)
		{
			put(string(key), value);
		}
		inline void put(const char* key, bool value)
		{
			put(string(key), value);
		}

		any& get(const char * key);
		any& get(const key_type& key);

		template <typename T> inline T& get_as(const char * key)
		{
			return get_as<T>(string(key));
		}
		template <typename T> inline T& get_as(const key_type& key)
		{
			return any_cast<T&>(*map_get(data, key));
		}

		string to_string() const;
	};

	//std::ostream& operator<< (std::ostream& stream, const HeteroMap& hm);

	//////////////////////////////////////////////////////////////////////////

	namespace packers
	{
		class HeteroMapPacker : public IPacker
		{
		protected:
			int32_t id;
			const IPacker& get_packer(int32_t packerid) const;

		public:
			map<int32_t, IPacker*> packers_map;
			typedef HeteroMap data_type;

			HeteroMapPacker(int32_t id);

			virtual int32_t get_id() const;

			void pack(const HeteroMap& obj, ITransport& transport) const;
			void unpack(HeteroMap& obj, ITransport& transport) const;

			virtual void pack_any(const any& obj, ITransport& transport) const;
			virtual any unpack_any(ITransport& transport) const;
			virtual any unpack_shared(ITransport& transport) const;
		};

		extern HeteroMapPacker builtin_heteromap_packer;
	}
}



#endif // AGNOS_HETEROMAP_HPP_INCLUDED
