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

	/**
	 * a std::map-like object that can store heterogeneous keys and values.
	 * more specifically, the keys can be any of {bool, int32, int64, double,
	 * string, datetime}, and the values can be anything that boost::any can
	 * wrap.
	 *
	 * the HeteroMap associates with each key and value a packer object, which
	 * is used to serialize/deserialize the map
	 */
	class HeteroMap
	{
	public:
		/*
		 * for some reason, 'const char *' prefers to coerce itself to an int,
		 * rather than a std::string, when given the option, so we'll have to
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

		/**
		 * constructs an empty HeteroMap
		 */
		HeteroMap();

		/**
		 * constructs an new HeteroMap that is a copy of an existing HeteroMap
		 */
		HeteroMap(const HeteroMap& other);

		/**
		 * assignment operator
		 */
		HeteroMap& operator= (const HeteroMap& rhs);

		/**
		 * clears the entire map
		 */
		inline void clear()
		{
			data.clear();
		}
		/**
		 * checks if the map is empty
		 */
		inline bool empty() const
		{
			return data.empty();
		}
		/**
		 * returns the size of the map (number of key-value pairs)
		 */
		inline size_type size() const
		{
			return data.size();
		}
		/**
		 * removes the key-value pair with the given key
		 */
		inline size_type erase(const char * key)
		{
			return erase(string(key));
		}
		/**
		 * removes the key-value pair with the given key
		 */
		inline size_type erase(const key_type& key)
		{
			return data.erase(key);
		}
		/**
		 * returns a iterator that points to the first element
		 */
		inline iterator begin()
		{
			return data.begin();
		}
		/**
		 * returns a iterator that points to the first element
		 */
		inline const_iterator begin() const
		{
			return data.begin();
		}
		/**
		 * returns a iterator that points past the last element
		 */
		inline iterator end()
		{
			return data.end();
		}
		/**
		 * returns a iterator that points past the last element
		 */
		inline const_iterator end() const
		{
			return data.end();
		}
		/**
		 * returns a iterator that points the first instance of the given key
		 */
		inline iterator find(const char* key)
		{
			return find(string(key));
		}
		/**
		 * returns a iterator that points the first instance of the given key
		 */
		inline iterator find(const key_type& key)
		{
			return data.find(key);
		}
		/**
		 * returns a iterator that points the first instance of the given key
		 */
		inline const_iterator find(const char* key) const
		{
			return find(string(key));
		}
		/**
		 * returns a iterator that points the first instance of the given key
		 */
		inline const_iterator find(const key_type& key) const
		{
			return data.find(key);
		}
		/**
		 * checks whether the given key exists in the map
		 */
		inline bool contains(const char* key) const
		{
			return contains(string(key));
		}
		/**
		 * checks whether the given key exists in the map
		 */
		inline bool contains(const key_type& key) const
		{
			return find(key) != end();
		}

		/**
		 * adds the given key-value pair with the given key-packer and value-packer
		 */
		void put(const key_type& key, const IPacker& keypacker, const any& value, const IPacker& valpacker);

		/**
		 * adds the given key-value pair with the given key-packer and value-packer
		 */
		inline void put(const char * key, const IPacker& keypacker, const any& value, const IPacker& valpacker)
		{
			put(string(key), keypacker, value, valpacker);
		}

		/**
		 * specialized version of put
		 */
		inline void put(int32_t key, const char * value)
		{
			put(key, string(value));
		}
		/**
		 * specialized version of put
		 */
		inline void put(int32_t key, const string& value)
		{
			put(key, packers::int32_packer, value, packers::string_packer);
		}
		/**
		 * specialized version of put
		 */
		inline void put(int32_t key, int32_t value)
		{
			put(key, packers::int32_packer, value, packers::int32_packer);
		}
		/**
		 * specialized version of put
		 */
		inline void put(int32_t key, int64_t value)
		{
			put(key, packers::int32_packer, value, packers::int64_packer);
		}
		/**
		 * specialized version of put
		 */
		inline void put(int32_t key, double value)
		{
			put(key, packers::int32_packer, value, packers::float_packer);
		}
		/**
		 * specialized version of put
		 */
		inline void put(int32_t key, datetime value)
		{
			put(key, packers::int32_packer, value, packers::date_packer);
		}
		/**
		 * specialized version of put
		 */
		inline void put(int32_t key, bool value)
		{
			put(key, packers::int32_packer, value, packers::bool_packer);
		}

		/**
		 * specialized version of put
		 */
		inline void put(int64_t key, const char * value)
		{
			put(key, string(value));
		}
		/**
		 * specialized version of put
		 */
		inline void put(int64_t key, int32_t value)
		{
			put(key, packers::int64_packer, value, packers::int32_packer);
		}
		/**
		 * specialized version of put
		 */
		inline void put(int64_t key, int64_t value)
		{
			put(key, packers::int64_packer, value, packers::int64_packer);
		}
		/**
		 * specialized version of put
		 */
		inline void put(int64_t key, const string& value)
		{
			put(key, packers::int64_packer, value, packers::string_packer);
		}
		/**
		 * specialized version of put
		 */
		inline void put(int64_t key, double value)
		{
			put(key, packers::int64_packer, value, packers::float_packer);
		}
		/**
		 * specialized version of put
		 */
		inline void put(int64_t key, datetime value)
		{
			put(key, packers::int64_packer, value, packers::date_packer);
		}
		/**
		 * specialized version of put
		 */
		inline void put(int64_t key, bool value)
		{
			put(key, packers::int64_packer, value, packers::bool_packer);
		}

		/**
		 * specialized version of put
		 */
		inline void put(double key, const char * value)
		{
			put(key, string(value));
		}
		/**
		 * specialized version of put
		 */
		inline void put(double key, const string& value)
		{
			put(key, packers::float_packer, value, packers::string_packer);
		}
		/**
		 * specialized version of put
		 */
		inline void put(double key, int32_t value)
		{
			put(key, packers::float_packer, value, packers::int32_packer);
		}
		/**
		 * specialized version of put
		 */
		inline void put(double key, int64_t value)
		{
			put(key, packers::float_packer, value, packers::int64_packer);
		}
		/**
		 * specialized version of put
		 */
		inline void put(double key, double value)
		{
			put(key, packers::float_packer, value, packers::float_packer);
		}
		/**
		 * specialized version of put
		 */
		inline void put(double key, datetime value)
		{
			put(key, packers::float_packer, value, packers::date_packer);
		}
		/**
		 * specialized version of put
		 */
		inline void put(double key, bool value)
		{
			put(key, packers::float_packer, value, packers::bool_packer);
		}

		/**
		 * specialized version of put
		 */
		inline void put(const string& key, const char * value)
		{
			put(key, string(value));
		}
		/**
		 * specialized version of put
		 */
		inline void put(const string& key, int32_t value)
		{
			put(key, packers::string_packer, value, packers::int32_packer);
		}
		/**
		 * specialized version of put
		 */
		inline void put(const string& key, int64_t value)
		{
			put(key, packers::string_packer, value, packers::int64_packer);
		}
		/**
		 * specialized version of put
		 */
		inline void put(const string& key, const string& value)
		{
			put(key, packers::string_packer, value, packers::string_packer);
		}
		/**
		 * specialized version of put
		 */
		inline void put(const string& key, double value)
		{
			put(key, packers::string_packer, value, packers::float_packer);
		}
		/**
		 * specialized version of put
		 */
		inline void put(const string& key, datetime value)
		{
			put(key, packers::string_packer, value, packers::date_packer);
		}
		/**
		 * specialized version of put
		 */
		inline void put(const string& key, bool value)
		{
			put(key, packers::string_packer, value, packers::bool_packer);
		}

		/**
		 * specialized version of put
		 */
		inline void put(const char* key, const char * value)
		{
			put(string(key), string(value));
		}
		/**
		 * specialized version of put
		 */
		inline void put(const char* key, int32_t value)
		{
			put(string(key), value);
		}
		/**
		 * specialized version of put
		 */
		inline void put(const char* key, int64_t value)
		{
			put(string(key), value);
		}
		/**
		 * specialized version of put
		 */
		inline void put(const char* key, const string& value)
		{
			put(string(key), value);
		}
		/**
		 * specialized version of put
		 */
		inline void put(const char* key, double value)
		{
			put(string(key), value);
		}
		/**
		 * specialized version of put
		 */
		inline void put(const char* key, datetime value)
		{
			put(string(key), value);
		}
		/**
		 * specialized version of put
		 */
		inline void put(const char* key, bool value)
		{
			put(string(key), value);
		}

		/**
		 * a convenience method that inserts a new HeteroMap into this map,
		 * under the given key
		 */
		HeteroMap * put_new_map(const string& name);

		/**
		 * returns the value associated with the given key
		 */
		inline any& get(const HeteroMap::key_type& key)
		{
			return *map_get(data, key);
		}

		/**
		 * returns the value associated with the given key
		 */
		inline any& get(const char * key)
		{
			return get(string(key));
		}

		/**
		 * returns the value associated with the given key, casted to the given
		 * type
		 */
		template <typename T> inline T& get_as(const char * key)
		{
			return get_as<T>(string(key));
		}
		/**
		 * returns the value associated with the given key, casted to the given
		 * type
		 */
		template <typename T> inline T& get_as(const key_type& key)
		{
			return any_cast<T&>(*map_get(data, key));
		}

		/**
		 * returns a human-readable representation of the map's elements
		 */
		string to_string() const;
	};

	//std::ostream& operator<< (std::ostream& stream, const HeteroMap& hm);

	//////////////////////////////////////////////////////////////////////////

	namespace packers
	{
		/**
		 * the packer for HeteroMap instances
		 */
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
			inline void pack(const shared_ptr<HeteroMap> obj, ITransport& transport) const
			{
				pack(*obj, transport);
			}
			void unpack(HeteroMap& obj, ITransport& transport) const;

			virtual void pack_any(const any& obj, ITransport& transport) const;
			virtual any unpack_any(ITransport& transport) const;
			virtual any unpack_shared(ITransport& transport) const;
		};

		extern HeteroMapPacker builtin_heteromap_packer;
	}
}



#endif // AGNOS_HETEROMAP_HPP_INCLUDED
