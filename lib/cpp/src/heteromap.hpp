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

	DEFINE_EXCEPTION(HeteroMapError)

	class HeteroMap
	{
	public:
		typedef variant<int32_t, int64_t, string, datetime, double> key_type;
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
		inline iterator find(const key_type& key)
		{
			return data.find(key);
		}
		inline const_iterator find(const key_type& key) const
		{
			return data.find(key);
		}
		inline bool contains(const key_type& key) const
		{
			return find(key) != end();
		}

		void put(const key_type& key, const IPacker& keypacker, const any& value, const IPacker& valpacker);

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

		any& get(const key_type& key);

		template <typename T> inline T& get_as(const key_type& key)
		{
			return any_cast<T&>(*map_get(data, key));
		}
	};

	//////////////////////////////////////////////////////////////////////////

	namespace packers
	{
		class HeteroMapPacker : public IPacker
		{
		public:
			typedef map<int32_t, IPacker&> packers_map_type;
			typedef shared_ptr<packers_map_type> packers_map_ptr;
			typedef HeteroMap data_type;

		protected:
			int32_t id;
			packers_map_ptr packers_map;
			const IPacker& get_packer(int32_t packerid) const;

		public:
			HeteroMapPacker(int32_t id);
			HeteroMapPacker(int32_t id, packers_map_ptr packers_map);

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
