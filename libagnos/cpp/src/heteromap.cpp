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

#include "heteromap.hpp"


namespace agnos
{
	HeteroMap::HeteroMap() : data(), packers_info()
	{
	}

	HeteroMap::HeteroMap(const HeteroMap& other) : data(other.data), packers_info(other.packers_info)
	{
	}

	HeteroMap& HeteroMap::operator= (const HeteroMap& rhs)
	{
		data = rhs.data;
		packers_info = rhs.packers_info;
		return *this;
	}

	void HeteroMap::put(const HeteroMap::key_type& key, const IPacker& keypacker, const any& value, const IPacker& valpacker)
	{
		map_put(data, key, value);
		map_put(packers_info, key, PackerInfo(keypacker, valpacker));
	}

	inline any& HeteroMap::get(const HeteroMap::key_type& key)
	{
		return *map_get(data, key);
	}

	any& HeteroMap::get(const char * key)
	{
		return get(string(key));
	}

	/*std::ostream& operator<< (std::ostream& stream, const HeteroMap& hm)
	{
		stream << "{";
		for (HeteroMap::const_iterator it = hm.begin(); it != hm.end(); it++) {
			//stream << it->first << " : " << it->second << ", ";
			stream << it->first << " : " << "?" << ", ";
		}
		stream << "}";
		return stream;
	}*/
}


namespace agnos
{
	namespace packers
	{
		HeteroMapPacker::HeteroMapPacker(int32_t id) :
			id(id), packers_map()
		{
		}

		int32_t HeteroMapPacker::get_id() const
		{
			return id;
		}

		const IPacker& HeteroMapPacker::get_packer(int32_t packerid) const
		{
			switch (packerid)
			{
				case 1:
					return int8_packer;
				case 2:
					return bool_packer;
				case 3:
					return int16_packer;
				case 4:
					return int32_packer;
				case 5:
					return int64_packer;
				case 6:
					return float_packer;
				case 7:
					return buffer_packer;
				case 8:
					return date_packer;
				case 9:
					return string_packer;

				case 800:
					return list_of_int8_packer;
				case 801:
					return list_of_bool_packer;
				case 802:
					return list_of_int16_packer;
				case 803:
					return list_of_int32_packer;
				case 804:
					return list_of_int64_packer;
				case 805:
					return list_of_float_packer;
				case 806:
					return list_of_buffer_packer;
				case 807:
					return list_of_date_packer;
				case 808:
					return list_of_string_packer;

				case 820:
					return set_of_int8_packer;
				case 821:
					return set_of_bool_packer;
				case 822:
					return set_of_int16_packer;
				case 823:
					return set_of_int32_packer;
				case 824:
					return set_of_int64_packer;
				case 825:
					return set_of_float_packer;
				case 826:
					return set_of_buffer_packer;
				case 827:
					return set_of_date_packer;
				case 828:
					return set_of_string_packer;

				case 850:
					return map_of_int32_int32_packer;
				case 851:
					return map_of_int32_string_packer;
				case 852:
					return map_of_string_int32_packer;
				case 853:
					return map_of_string_string_packer;

				case 998:
					return builtin_heteromap_packer;

				default:
					IPacker** pkr = map_get(packers_map, packerid, false);
					if (pkr == NULL) {
						THROW_FORMATTED(HeteroMapError, "unknown packer id: " << packerid);
					}
					return **pkr;
			}
		}

		class HeteroMapKeyPackerVisitor : public boost::static_visitor<>
		{
		protected:
			const IPacker& pkr;
			ITransport& transport;

		public:
			HeteroMapKeyPackerVisitor(const IPacker& pkr, ITransport& transport) :
				pkr(pkr), transport(transport)
			{
			}

			template <typename T> void operator() (const T& obj) const
			{
				pkr.pack_any(obj, transport);
			}
		};

		void HeteroMapPacker::pack(const HeteroMap& obj, ITransport& transport) const
		{
			Int32Packer::pack(obj.size(), transport);

			for (HeteroMap::const_iterator it = obj.begin(); it != obj.end(); it++) {
				const HeteroMap::PackerInfo& pkr = obj.packers_info.find(it->first)->second;

				Int32Packer::pack(pkr.keypacker.get_id(), transport);
				HeteroMapKeyPackerVisitor visitor(pkr.keypacker, transport);
				boost::apply_visitor(visitor, it->first);

				Int32Packer::pack(pkr.valpacker.get_id(), transport);
				pkr.valpacker.pack_any(it->second, transport);
			}
		}

		void HeteroMapPacker::unpack(HeteroMap& obj, ITransport& transport) const
		{
			int32_t size;
			Int32Packer::unpack(size, transport);

			obj.clear();

			for (int i = 0; i < size; i++) {
				int32_t key_id, val_id;

				Int32Packer::unpack(key_id, transport);

				const IPacker& key_pkr = get_packer(key_id);
				any _key = key_pkr.unpack_any(transport);
				HeteroMap::key_type key;

				if (_key.type() == typeid(string)) {
					key = any_cast<string>(_key);
				}
				else if (_key.type() == typeid(int32_t)) {
					key = any_cast<int32_t>(_key);
				}
				else if (_key.type() == typeid(int64_t)) {
					key = any_cast<int64_t>(_key);
				}
				else if (_key.type() == typeid(double)) {
					key = any_cast<double>(_key);
				}
				else if (_key.type() == typeid(bool)) {
					key = any_cast<bool>(_key);
				}
				else if (_key.type() == typeid(datetime)) {
					key = any_cast<datetime>(_key);
				}
				else {
					THROW_FORMATTED(HeteroMapError,
							"[HeteroMapPacker::unpack] key is of an unsupported type: " << _key.type().name());
				}

				Int32Packer::unpack(val_id, transport);
				const IPacker& val_pkr = get_packer(val_id);
				any value = val_pkr.unpack_any(transport);

				obj.put(key, key_pkr, value, val_pkr);
			}
		}

		void HeteroMapPacker::pack_any(const any& obj, ITransport& transport) const
		{
			if (obj.type() == typeid(shared_ptr<HeteroMap>)) {
				shared_ptr<HeteroMap> tmp = any_cast< shared_ptr<HeteroMap> >(obj);
				pack(*tmp, transport);
			}
			else {
				const HeteroMap &tmp = any_cast<HeteroMap>(obj);
				pack(tmp, transport);
			}
		}

		any HeteroMapPacker::unpack_any(ITransport& transport) const
		{
			HeteroMap obj;
			unpack(obj, transport);
			return obj;
		}

		any HeteroMapPacker::unpack_shared(ITransport& transport) const
		{
			shared_ptr<HeteroMap> obj(new HeteroMap());
			unpack(*obj, transport);
			return obj;
		}

		HeteroMapPacker builtin_heteromap_packer(998);
	}

}



