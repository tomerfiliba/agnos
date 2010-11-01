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

#ifndef AGNOS_PACKERS_HPP_INCLUDED
#define AGNOS_PACKERS_HPP_INCLUDED

#include "objtypes.hpp"
#include "transports.hpp"
#include "utils.hpp"

namespace agnos
{
	namespace packers
	{
		using agnos::transports::ITransport;

		DEFINE_EXCEPTION(PackerError);

		class IPacker : public boost::noncopyable
		{
		public:
			virtual int32_t get_id() const = 0;
			virtual void pack_any(const any& obj, ITransport& transport) const = 0;
			virtual any unpack_any(ITransport& transport) const = 0;
			virtual any unpack_shared(ITransport& transport) const = 0;

			template<typename T> T unpack_as(ITransport& transport) const
			{
				any res = unpack_any(transport);
				DEBUG_LOG("res is " << res.type().name());
				return any_cast<T>(unpack_any(transport));
			}
		};

		#define IPACKER_SIMPLE_DECL(CLS, TYPE, ID) \
			CLS(); \
			static const int _id = ID; \
			typedef TYPE data_type; \
			int32_t get_id() const; \
			void pack_any(const any& obj, ITransport& transport) const; \
			any unpack_any(ITransport& transport) const; \
			any unpack_shared(ITransport& transport) const; \
			static void pack(shared_ptr<data_type> obj, ITransport& transport); \
			static void unpack(shared_ptr<data_type>& obj, ITransport& transport); \
			static void pack(const data_type& obj, ITransport& transport); \
			static void unpack(data_type& obj, ITransport& transport);

		#define IPACKER_TEMPLATED_DECL(TYPE) \
			typedef TYPE data_type; \
			int32_t get_id() const \
			{ \
				return ID; \
			} \
			void pack_any(const any& obj, ITransport& transport) const \
			{ \
				if (obj.type() == typeid(shared_ptr<data_type>)) { \
					shared_ptr<data_type> tmp = any_cast< shared_ptr<data_type> >(obj); \
					pack(*tmp, transport); \
				} \
				else { \
					pack(any_cast<data_type>(obj), transport); \
				} \
			} \
			any unpack_any(ITransport& transport) const \
			{ \
				data_type tmp; \
				unpack(tmp, transport); \
				return tmp; \
			} \
			any unpack_shared(ITransport& transport) const \
			{ \
				shared_ptr<data_type> obj(new data_type()); \
				unpack(*obj, transport); \
				return obj; \
			} \
			void pack(shared_ptr<data_type> obj, ITransport& transport) const \
			{ \
				pack(*obj, transport); \
			} \
			void unpack(shared_ptr<data_type>& obj, ITransport& transport) const \
			{ \
				obj.reset(new TYPE()); \
				unpack(*obj, transport); \
			}

		//////////////////////////////////////////////////////////////////////

		class VoidPacker :  public IPacker
		{
		public:
			int32_t get_id() const;
			void pack_any(const any& obj, ITransport& transport) const;
			any unpack_any(ITransport& transport) const;
			any unpack_shared(ITransport& transport) const;
		};

		extern VoidPacker void_packer;

		//////////////////////////////////////////////////////////////////////

		class Int8Packer :  public IPacker
		{
		public:
			IPACKER_SIMPLE_DECL(Int8Packer, int8_t, 1);
		};

		extern Int8Packer int8_packer;

		//////////////////////////////////////////////////////////////////////

		class BoolPacker :  public IPacker
		{
		public:
			IPACKER_SIMPLE_DECL(BoolPacker, bool, 2);

            static void unpack(std::_Bit_reference obj, ITransport& transport);
		};

		extern BoolPacker bool_packer;

		//////////////////////////////////////////////////////////////////////

		class Int16Packer :  public IPacker
		{
		public:
			IPACKER_SIMPLE_DECL(Int16Packer, int16_t, 3);
		};

		extern Int16Packer int16_packer;

		//////////////////////////////////////////////////////////////////////

		class Int32Packer :  public IPacker
		{
		public:
			IPACKER_SIMPLE_DECL(Int32Packer, int32_t, 4);
		};

		extern Int32Packer int32_packer;

		//////////////////////////////////////////////////////////////////////

		class Int64Packer :  public IPacker
		{
		public:
			IPACKER_SIMPLE_DECL(Int64Packer, int64_t, 5);
		};

		extern Int64Packer int64_packer;

		//////////////////////////////////////////////////////////////////////

		class FloatPacker :  public IPacker
		{
		public:
			IPACKER_SIMPLE_DECL(FloatPacker, double, 6);
		};

		extern FloatPacker float_packer;

		//////////////////////////////////////////////////////////////////////

		class BufferPacker :  public IPacker
		{
		public:
			IPACKER_SIMPLE_DECL(BufferPacker, string, 7);
		};

		extern BufferPacker buffer_packer;

		//////////////////////////////////////////////////////////////////////

		class DatePacker :  public IPacker
		{
		public:
			IPACKER_SIMPLE_DECL(DatePacker, datetime, 8);
		};

		extern DatePacker date_packer;

		//////////////////////////////////////////////////////////////////////

		class StringPacker :  public IPacker
		{
		public:
			IPACKER_SIMPLE_DECL(StringPacker, string, 9);
		};

		extern StringPacker string_packer;

		//////////////////////////////////////////////////////////////////////

		class _NullObj : public boost::noncopyable
		{
		};

		extern shared_ptr<_NullObj> NullObj;

		class NullPacker :  public IPacker
		{
		public:
			int32_t get_id() const;
			void pack_any(const any& obj, ITransport& transport) const;
			any unpack_any(ITransport& transport) const;
			any unpack_shared(ITransport& transport) const;
		};

		extern NullPacker null_packer;

		//////////////////////////////////////////////////////////////////////

		template<typename TYPE, int ID> class ListPacker :  public IPacker
		{
		protected:
			const IPacker& packer;

		public:
			typedef TYPE element_type;
			IPACKER_TEMPLATED_DECL(vector<element_type>);

			ListPacker(IPacker& packer) : packer(packer)
			{
			}

			void pack(const data_type& obj, ITransport& transport) const
			{
				int32_t size = obj.size();
				Int32Packer::pack(size, transport);
				for (int i = 0; i < size; i++) {
					packer.pack_any(obj[i], transport);
				}
			}

			void unpack(data_type& obj, ITransport& transport) const
			{
				int32_t size;
				Int32Packer::unpack(size, transport);
				obj.clear();
				obj.reserve(size);
				for (int i = 0; i < size; i++) {
					obj.push_back(packer.unpack_as<element_type>(transport));
				}
			}
		};

		extern ListPacker<int8_t, 800> list_of_int8_packer;
		extern ListPacker<bool, 801> list_of_bool_packer;
		extern ListPacker<int16_t, 802> list_of_int16_packer;
		extern ListPacker<int32_t, 803> list_of_int32_packer;
		extern ListPacker<int64_t, 804> list_of_int64_packer;
		extern ListPacker<double, 805> list_of_float_packer;
		extern ListPacker<string, 806> list_of_buffer_packer;
		extern ListPacker<datetime, 807> list_of_date_packer;
		extern ListPacker<string, 808> list_of_string_packer;

		//////////////////////////////////////////////////////////////////////

		template<typename TYPE, int ID> class SetPacker :  public IPacker
		{
		protected:
			const IPacker& packer;

		public:
			typedef TYPE element_type;
			IPACKER_TEMPLATED_DECL(set<element_type>);

			SetPacker(IPacker& packer) : packer(packer)
			{
			}

			void pack(const data_type& obj, ITransport& transport) const
			{
				Int32Packer::pack(obj.size(), transport);
				typename data_type::const_iterator it;
				for (it = obj.begin(); it != obj.end(); it++) {
					packer.pack_any(*it, transport);
				}
			}

			void unpack(data_type& obj, ITransport& transport) const
			{
				int32_t size;
				Int32Packer::unpack(size, transport);
				obj.clear();
				for (int i = 0; i < size; i++) {
					obj.insert(packer.unpack_as<element_type>(transport));
				}
			}
		};

		extern SetPacker<int8_t, 820> set_of_int8_packer;
		extern SetPacker<bool, 821> set_of_bool_packer;
		extern SetPacker<int16_t, 822> set_of_int16_packer;
		extern SetPacker<int32_t, 823> set_of_int32_packer;
		extern SetPacker<int64_t, 824> set_of_int64_packer;
		extern SetPacker<double, 825> set_of_float_packer;
		extern SetPacker<string, 826> set_of_buffer_packer;
		extern SetPacker<datetime, 827> set_of_date_packer;
		extern SetPacker<string, 828> set_of_string_packer;

		//////////////////////////////////////////////////////////////////////

		template<typename KEYTYPE, typename VALTYPE, int ID> class MapPacker :  public IPacker
		{
		public:
			typedef KEYTYPE key_type;
			typedef VALTYPE val_type;

		protected:
			typedef map<key_type, val_type> _datatype;
			const IPacker& key_packer;
			const IPacker& val_packer;

		public:
			IPACKER_TEMPLATED_DECL(_datatype);

			MapPacker(const IPacker& key_packer, const IPacker& val_packer) : key_packer(key_packer), val_packer(val_packer)
			{
			}

			void pack(const data_type& obj, ITransport& transport) const
			{
				Int32Packer::pack(obj.size(), transport);
				typename data_type::const_iterator it;
				for (it = obj.begin(); it != obj.end(); it++) {
					key_packer.pack_any(it->first, transport);
					val_packer.pack_any(it->second, transport);
				}
			}

			void unpack(data_type& obj, ITransport& transport) const
			{
				int32_t size;
				Int32Packer::unpack(size, transport);
				obj.clear();
				for (int i = 0; i < size; i++) {
					key_type k = key_packer.unpack_as<key_type>(transport);
					val_type v = val_packer.unpack_as<val_type>(transport);
					map_put(obj, k, v);
				}
			}
		};

		extern MapPacker<int32_t, int32_t, 850> map_of_int32_int32_packer;
		extern MapPacker<int32_t, string, 851> map_of_int32_string_packer;
		extern MapPacker<string, int32_t, 852> map_of_string_int32_packer;
		extern MapPacker<string, string, 853> map_of_string_string_packer;

		//////////////////////////////////////////////////////////////////////

		#define RECORD_PACKER_IMPL(TYPE, ID) \
			typedef TYPE data_type; \
			int32_t get_id() const \
			{ \
				return ID; \
			} \
			void pack_any(const any& obj, ITransport& transport) const \
			{ \
				if (obj.type() == typeid(shared_ptr<data_type>)) { \
					shared_ptr<data_type> tmp = any_cast< shared_ptr<data_type> >(obj); \
					pack(*tmp, transport); \
				} \
				else { \
					pack(any_cast<data_type>(obj), transport); \
				} \
			} \
			any unpack_any(ITransport& transport) const \
			{ \
				data_type tmp; \
				unpack(tmp, transport); \
				return tmp; \
			} \
			any unpack_shared(ITransport& transport) const \
			{ \
				shared_ptr<data_type> obj(new data_type()); \
				unpack(*obj, transport); \
				return obj; \
			} \
			void pack(shared_ptr<data_type> obj, ITransport& transport) const \
			{ \
				pack(*obj, transport); \
			} \
			void unpack(shared_ptr<data_type>& obj, ITransport& transport) const \
			{ \
				obj.reset(new TYPE()); \
				unpack(*obj, transport); \
			}


		//////////////////////////////////////////////////////////////////////

		class ISerializer
		{
		public:
			virtual objref_t store(objref_t oid, any obj) = 0;
			virtual any load(objref_t oid) = 0;
		};

		//--

		template<typename TYPE, int ID> class ObjrefPacker :  public IPacker
		{
		public:
			typedef shared_ptr<TYPE> data_type;

		protected:
			ISerializer& ser;

			objref_t get_oid(data_type obj) const
			{
				return (objref_t)((intptr_t)(obj.get()));
			}

		public:
			ObjrefPacker(ISerializer& ser) : ser(ser)
			{
			}

			int32_t get_id() const
			{
				return ID;
			}

			//--

			void pack(data_type obj, ITransport& transport) const
			{
				DEBUG_LOG("ObjrefPacker::pack of " << (intptr_t)obj.get());
				objref_t oid = get_oid(obj);
				oid = ser.store(oid, obj);
				int64_packer.pack(oid, transport);
			}

			void pack_any(const any& obj, ITransport& transport) const
			{
				pack(any_cast<data_type>(obj), transport);
			}

			//--

			void unpack(data_type& obj, ITransport& transport) const
			{
				objref_t oid;
				int64_packer.unpack(oid, transport);
				DEBUG_LOG("ObjrefPacker::unpack of " << oid);
				obj = any_cast<data_type>(ser.load(oid));
			}

			any unpack_any(ITransport& transport) const
			{
				objref_t oid;
				int64_packer.unpack(oid, transport);
				return ser.load(oid);
			}

			any unpack_shared(ITransport& transport) const
			{
				return unpack_any(transport);
			}
		};


	}
}






#endif // AGNOS_PACKERS_HPP_INCLUDED
