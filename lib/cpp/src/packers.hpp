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

		class IPacker
		{
		public:
			virtual int32_t get_id() const = 0;
			virtual void pack_any(const any& obj, ITransport& transport) const = 0;
			virtual any unpack_any(ITransport& transport) const = 0;
			virtual any unpack_shared(ITransport& transport) const = 0;
			template<typename T> T unpack_as(ITransport& transport) const
			{
				return any_cast<T>(unpack_any(transport));
			}
		};

		#define IPACKER_SIMPLE_DECL(CLS, TYPE, ID) \
			CLS(); \
			static const int _id = ID; \
			typedef TYPE data_type; \
			virtual int32_t get_id() const; \
			virtual void pack_any(const any& obj, ITransport& transport) const; \
			virtual any unpack_any(ITransport& transport) const; \
			virtual any unpack_shared(ITransport& transport) const; \
			static void pack(shared_ptr<data_type> obj, ITransport& transport); \
			static void unpack(shared_ptr<data_type>& obj, ITransport& transport); \
			static void pack(const data_type& obj, ITransport& transport); \
			static void unpack(data_type& obj, ITransport& transport);

		#define IPACKER_TEMPLATED_DECL(CLS, TYPE, ID) \
			typedef TYPE data_type; \
			CLS() {} \
			virtual int32_t get_id() const \
			{ \
				return ID; \
			} \
			virtual void pack_any(const any& obj, ITransport& transport) const \
			{ \
				if (obj.type() == typeid(shared_ptr<data_type>)) { \
					shared_ptr<data_type> tmp = any_cast< shared_ptr<data_type> >(obj); \
					pack(*tmp, transport); \
				} \
				else { \
					pack(any_cast<data_type>(obj), transport); \
				} \
			} \
			virtual any unpack_any(ITransport& transport) const \
			{ \
				data_type tmp; \
				unpack(tmp, transport); \
				return tmp; \
			} \
			virtual any unpack_shared(ITransport& transport) const \
			{ \
				shared_ptr<data_type> obj(new data_type()); \
				unpack(*obj, transport); \
				return obj; \
			} \
			static void pack(shared_ptr<data_type> obj, ITransport& transport) \
			{ \
				pack(*obj, transport); \
			} \
			static void unpack(shared_ptr<data_type>& obj, ITransport& transport) \
			{ \
				obj.reset(new TYPE()); \
				unpack(*obj, transport); \
			}

		//////////////////////////////////////////////////////////////////////

		class VoidPacker :  public IPacker
		{
		public:
			virtual int32_t get_id() const;
			virtual void pack_any(const any& obj, ITransport& transport) const;
			virtual any unpack_any(ITransport& transport) const;
			virtual any unpack_shared(ITransport& transport) const;
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

		template<typename PKR, int ID> class ListPacker :  public IPacker
		{
		public:
			typedef typename PKR::data_type element_type;
			IPACKER_TEMPLATED_DECL(ListPacker, vector<element_type>, ID);

			static void pack(const data_type& obj, ITransport& transport)
			{
				int32_t size = obj.size();
				Int32Packer::pack(size, transport);
				for (int i = 0; i < size; i++) {
					PKR::pack(obj[i], transport);
				}
			}

			static void unpack(data_type& obj, ITransport& transport)
			{
				int32_t size;
				Int32Packer::unpack(size, transport);
				obj.resize(size);
				for (int i = 0; i < size; i++) {
					PKR::unpack(obj[i], transport);
				}
			}
		};

		#define LIST_OF(PKR, ID, NAME) \
			typedef ListPacker<PKR, ID> ListOf ## PKR; \
			extern ListOf ## PKR list_of_ ## NAME ## _packer
		LIST_OF(Int8Packer, 800, int8);
		LIST_OF(BoolPacker, 801, bool);
		LIST_OF(Int16Packer, 802, int16);
		LIST_OF(Int32Packer, 803, int32);
		LIST_OF(Int64Packer, 804, int64);
		LIST_OF(FloatPacker, 805, float);
		LIST_OF(BufferPacker, 806, buffer);
		LIST_OF(DatePacker, 807, date);
		LIST_OF(StringPacker, 808, string);
		#undef LIST_OF

		//////////////////////////////////////////////////////////////////////

		template<typename PKR, int ID> class SetPacker :  public IPacker
		{
		public:
			typedef typename PKR::data_type element_type;
			IPACKER_TEMPLATED_DECL(SetPacker, set<element_type>, ID);

			static void pack(const data_type& obj, ITransport& transport)
			{
				Int32Packer::pack(obj.size(), transport);
				typename data_type::const_iterator it;
				for (it = obj.begin(); it != obj.end(); it++) {
					PKR::pack(*it, transport);
				}
			}

			static void unpack(data_type& obj, ITransport& transport)
			{
				int32_t size;
				Int32Packer::unpack(size, transport);
				obj.clear();
				for (int i = 0; i < size; i++) {
					element_type tmp;
					PKR::unpack(tmp, transport);
					obj.insert(tmp);
				}
			}
		};

		#define SET_OF(PKR, ID, NAME) \
			typedef SetPacker<PKR, ID> SetOf ## PKR; \
			extern SetOf ## PKR set_of_ ## NAME ## _packer
		SET_OF(Int8Packer, 820, int8);
		SET_OF(BoolPacker, 821, bool);
		SET_OF(Int16Packer, 822, int16);
		SET_OF(Int32Packer, 823, int32);
		SET_OF(Int64Packer, 824, int64);
		SET_OF(FloatPacker, 825, float);
		SET_OF(BufferPacker, 826, buffer);
		SET_OF(DatePacker, 827, date);
		SET_OF(StringPacker, 828, string);
		#undef SET_OF

		//////////////////////////////////////////////////////////////////////

		template<typename KEYPKR, typename VALPKR, int ID> class MapPacker :  public IPacker
		{
		public:
			typedef typename KEYPKR::data_type key_type;
			typedef typename VALPKR::data_type val_type;
		protected:
			typedef map<key_type, val_type> _datatype;
		public:
			IPACKER_TEMPLATED_DECL(MapPacker, _datatype, ID);

			static void pack(const data_type& obj, ITransport& transport)
			{
				Int32Packer::pack(obj.size(), transport);
				typename data_type::const_iterator it;
				for (it = obj.begin(); it != obj.end(); it++) {
					KEYPKR::pack(it->first, transport);
					VALPKR::pack(it->second, transport);
				}
			}

			static void unpack(data_type& obj, ITransport& transport)
			{
				int32_t size;
				Int32Packer::unpack(size, transport);
				obj.clear();
				for (int i = 0; i < size; i++) {
					key_type k;
					val_type v;
					KEYPKR::unpack(k, transport);
					VALPKR::unpack(v, transport);
					obj.insert(typename data_type::value_type(k, v));
				}
			}
		};

		typedef MapPacker<Int32Packer, Int32Packer, 850> MapOfInt32Int32Packer;
		extern MapOfInt32Int32Packer map_of_int32_int32_packer;

		typedef MapPacker<Int32Packer, StringPacker, 851> MapOfInt32StringPacker;
		extern MapOfInt32StringPacker map_of_int32_string_packer;

		typedef MapPacker<StringPacker, Int32Packer, 852> MapOfStringInt32Packer;
		extern MapOfStringInt32Packer map_of_string_int32_packer;

		typedef MapPacker<StringPacker, StringPacker, 853> MapOfStringStringPacker;
		extern MapOfStringStringPacker map_of_string_string_packer;


		//////////////////////////////////////////////////////////////////////

		class ISerializer
		{
		public:
			virtual void store(objref_t oid, any obj) = 0;
			virtual any load(objref_t oid) = 0;
		};

		//--

		template<typename T, int ID> class ObjrefPacker :  public IPacker
		{
		public:
			typedef shared_ptr<T> data_type;

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

			virtual int32_t get_id() const
			{
				return ID;
			}

			//--

			void pack(data_type obj, ITransport& transport) const
			{
				objref_t oid = get_oid(obj);
				ser.store(oid, obj);
				int64_packer.pack(oid, transport);
			}

			virtual void pack_any(const any& obj, ITransport& transport) const
			{
				pack(any_cast<data_type>(obj), transport);
			}

			//--

			void unpack(data_type& obj, ITransport& transport) const
			{
				objref_t oid;
				int64_packer.unpack(oid, transport);
				obj = any_cast<data_type>(ser.load(oid));
			}

			virtual any unpack_any(ITransport& transport) const
			{
				objref_t oid;
				int64_packer.unpack(oid, transport);
				return ser.load(oid);
			}

			virtual any unpack_shared(ITransport& transport) const
			{
				return unpack_any(transport);
			}
		};


	}
}






#endif // AGNOS_PACKERS_HPP_INCLUDED
