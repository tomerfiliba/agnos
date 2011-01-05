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

#include "packers.hpp"
#include <boost/detail/endian.hpp>

#if defined(BOOST_BIG_ENDIAN)
#	ifndef ntohs
#		define ntohs(n) (n)
#		define htons(n) (n)
#	endif
#	ifndef ntohl
#		define ntohl(n) (n)
#		define htonl(n) (n)
#	endif
#	ifndef ntohll
#		define ntohll(n) (n)
#		define htonll(n) (n)
#	endif
#elif defined(BOOST_LITTLE_ENDIAN)

static inline int16_t _bswap_16(int16_t n)
{
	return ((n & 0x00ffu) << 8) | ((n & 0xff00u) >> 8);
}

static inline int32_t _bswap_32(int32_t n)
{
	return ((n & 0x000000fful) << 24) | ((n & 0x0000ff00ul) << 8) | ((n
	        & 0x00ff0000ul) >> 8) | ((n & 0xff000000ul) >> 24);
}

static inline int64_t _bswap_64(int64_t n)
{
	return ((n & 0xff00000000000000ull) >> 56) | ((n & 0x00ff000000000000ull)
	        >> 40) | ((n & 0x0000ff0000000000ull) >> 24) | ((n
	        & 0x000000ff00000000ull) >> 8) | ((n & 0x00000000ff000000ull) << 8)
	        | ((n & 0x0000000000ff0000ull) << 24)
	        | ((n & 0x000000000000ff00ull) << 40)
	        | ((n & 0x00000000000000ffull) << 56);
}

#	ifndef ntohs
#		define ntohs(n)  _bswap_16(n)
#		define htons(n)  _bswap_16(n)
#	endif
#	ifndef ntohl
#		define ntohl(n)  _bswap_32(n)
#		define htonl(n)  _bswap_32(n)
#	endif
#	ifndef ntohll
#		define ntohll(n) _bswap_64(n)
#		define htonll(n) _bswap_64(n)
#	endif
#else
#	error "unknown machine endianity"
#endif // BOOST_BYTE_ORDER

#define IPACKER_SIMPLE_IMPL(CLS, NAME) \
	CLS::CLS() {} \
	int32_t CLS::get_id() const \
	{ \
		return _id; \
	} \
	void CLS::pack_any(const any& obj, ITransport& transport) const \
	{ \
		if (obj.type() == typeid(shared_ptr<data_type>)) { \
			shared_ptr<data_type> tmp = any_cast< shared_ptr<data_type> >(obj); \
			pack(*tmp, transport); \
		} \
		else { \
			pack(any_cast<data_type>(obj), transport); \
		} \
	} \
	any CLS::unpack_any(ITransport& transport) const \
	{ \
		data_type tmp; \
		unpack(tmp, transport); \
		return tmp; \
	} \
	any CLS::unpack_shared(ITransport& transport) const \
	{ \
		shared_ptr<data_type> obj(new data_type()); \
		unpack(*obj, transport); \
		return obj; \
	} \
	void CLS::pack(shared_ptr<CLS::data_type> obj, ITransport& transport) \
	{ \
		pack(*obj, transport); \
	} \
	void CLS::unpack(shared_ptr<CLS::data_type>& obj, ITransport& transport) \
	{ \
		obj.reset(new data_type()); \
		unpack(*obj, transport); \
	} \
	CLS NAME;

//////////////////////////////////////////////////////////////////////////////

namespace agnos
{
	namespace packers
	{
		inline static void _write(ITransport& transport, const char * buf,
		        size_t size)
		{
			transport.write(buf, size);
		}

		inline static void _read(ITransport& transport, char * buf, size_t size)
		{
			size_t total_got = 0;
			while (total_got < size) {
				size_t got = transport.read(buf + total_got, size - total_got);
				total_got += got;
				if (got <= 0 && total_got < size) {
					throw PackerError("unexpected EOF");
				}
			}
		}

		//////////////////////////////////////////////////////////////////////

		int32_t VoidPacker::get_id() const
		{
			throw PackerError("VoidPacker");
		}
		void VoidPacker::pack_any(const any& obj, ITransport& transport) const
		{
			throw PackerError("VoidPacker");
		}
		any VoidPacker::unpack_any(ITransport& transport) const
		{
			throw PackerError("VoidPacker");
		}
		any VoidPacker::unpack_shared(ITransport& transport) const
		{
			throw PackerError("VoidPacker");
		}

		VoidPacker void_packer;

		//////////////////////////////////////////////////////////////////////

		shared_ptr<_NullObj> NullObj;

		int32_t NullPacker::get_id() const
		{
			return 10;
		}
		void NullPacker::pack_any(const any& obj, ITransport& transport) const
		{
		}
		any NullPacker::unpack_any(ITransport& transport) const
		{
			return NullObj;
		}
		any NullPacker::unpack_shared(ITransport& transport) const
		{
			return NullObj;
		}

		NullPacker null_packer;

		//////////////////////////////////////////////////////////////////////

		IPACKER_SIMPLE_IMPL(Int8Packer, int8_packer)

		void Int8Packer::pack(const int8_t& obj, ITransport& transport)
		{
			_write(transport, (const char *) &obj, sizeof(obj));
		}

		void Int8Packer::unpack(int8_t& obj, ITransport& transport)
		{
			_read(transport, (char *) &obj, sizeof(obj));
		}

		//////////////////////////////////////////////////////////////////////

		IPACKER_SIMPLE_IMPL(BoolPacker, bool_packer)

		void BoolPacker::pack(const bool& obj, ITransport& transport)
		{
			int8_t tmp = obj ? 1 : 0;
			Int8Packer::pack(tmp, transport);
		}

		void BoolPacker::unpack(bool& obj, ITransport& transport)
		{
			int8_t tmp;
			Int8Packer::unpack(tmp, transport);
			obj = (tmp != 0);
		}

		void BoolPacker::unpack(std::_Bit_reference obj, ITransport& transport)
		{
			bool tmp;
			unpack(tmp, transport);
			obj = tmp;
		}

		//////////////////////////////////////////////////////////////////////

		IPACKER_SIMPLE_IMPL(Int16Packer, int16_packer)

		void Int16Packer::pack(const int16_t& obj, ITransport& transport)
		{
			int16_t tmp = htons(obj);
			_write(transport, (const char *) &tmp, sizeof(tmp));
		}

		void Int16Packer::unpack(int16_t& obj, ITransport& transport)
		{
			int16_t tmp;
			_read(transport, (char *) &tmp, sizeof(tmp));
			obj = ntohs(tmp);
		}

		//////////////////////////////////////////////////////////////////////

		IPACKER_SIMPLE_IMPL(Int32Packer, int32_packer)

		void Int32Packer::pack(const int32_t& obj, ITransport& transport)
		{
			int32_t tmp = htonl(obj);
			_write(transport, (const char*) &tmp, sizeof(tmp));
		}
		void Int32Packer::unpack(int32_t& obj, ITransport& transport)
		{
			int32_t tmp;
			_read(transport, (char*) &tmp, sizeof(tmp));
			obj = ntohl(tmp);
		}

		//////////////////////////////////////////////////////////////////////

		IPACKER_SIMPLE_IMPL(Int64Packer, int64_packer)

		void Int64Packer::pack(const int64_t& obj, ITransport& transport)
		{
			int64_t tmp = htonll(obj);
			transport.write((const char*) &tmp, sizeof(tmp));
		}
		void Int64Packer::unpack(int64_t& obj, ITransport& transport)
		{
			int64_t tmp;
			transport.read((char*) &tmp, sizeof(tmp));
			obj = ntohll(tmp);
		}

		//////////////////////////////////////////////////////////////////////

		IPACKER_SIMPLE_IMPL(FloatPacker, float_packer)

		void FloatPacker::pack(const double& obj, ITransport& transport)
		{
			int64_t tmp = *(reinterpret_cast<const int64_t*>(&obj));
			Int64Packer::pack(tmp, transport);
		}

		void FloatPacker::unpack(double& obj, ITransport& transport)
		{
			int64_t tmp;
			Int64Packer::unpack(tmp, transport);
			obj = *(reinterpret_cast<double*>(&tmp));
		}

		//////////////////////////////////////////////////////////////////////

		IPACKER_SIMPLE_IMPL(BufferPacker, buffer_packer)

		void BufferPacker::pack(const string& obj, ITransport& transport)
		{
			Int32Packer::pack(obj.size(), transport);
			transport.write(obj.data(), obj.size());
		}
		void BufferPacker::unpack(string& obj, ITransport& transport)
		{
			int32_t size;
			Int32Packer::unpack(size, transport);
			obj.resize(size);
			transport.read(const_cast<char*> (obj.data()), size);
		}

		//////////////////////////////////////////////////////////////////////

		IPACKER_SIMPLE_IMPL(StringPacker, string_packer)

		void StringPacker::pack(const string& obj, ITransport& transport)
		{
			BufferPacker::pack(obj, transport);
		}
		void StringPacker::unpack(string& obj, ITransport& transport)
		{
			BufferPacker::unpack(obj, transport);
		}

		//////////////////////////////////////////////////////////////////////

		IPACKER_SIMPLE_IMPL(DatePacker, date_packer)

		const int64_t microsecs_from_epoch = 44148153600000000ll;
		static datetime mintime = boost::posix_time::from_iso_string(
		        std::string("14000101T000000"));

		void DatePacker::pack(const datetime& obj, ITransport& transport)
		{
			timespan dur = obj - mintime;
			int64_t microsecs = dur.total_microseconds() + microsecs_from_epoch;
			Int64Packer::pack(microsecs, transport);
		}

		void DatePacker::unpack(datetime& obj, ITransport& transport)
		{
			int64_t val;
			Int64Packer::unpack(val, transport);
			val -= microsecs_from_epoch;

			// urrgh, boost::posix_time::microseconds only accepts int32!
			// need to do it the hard way
			timespan dur = boost::posix_time::microseconds(val % 1000000);
			val /= 1000000;
			dur += boost::posix_time::seconds(val % 60);
			val /= 60;
			dur += boost::posix_time::minutes(val % 60);
			val /= 60;
			dur += boost::posix_time::hours(val);

			obj = mintime + dur;
		}

		//////////////////////////////////////////////////////////////////////

		ListPacker<int8_t, 800> list_of_int8_packer(int8_packer);
		ListPacker<bool, 801> list_of_bool_packer(bool_packer);
		ListPacker<int16_t, 802> list_of_int16_packer(int16_packer);
		ListPacker<int32_t, 803> list_of_int32_packer(int32_packer);
		ListPacker<int64_t, 804> list_of_int64_packer(int64_packer);
		ListPacker<double, 805> list_of_float_packer(float_packer);
		ListPacker<string, 806> list_of_buffer_packer(buffer_packer);
		ListPacker<datetime, 807> list_of_date_packer(date_packer);
		ListPacker<string, 808> list_of_string_packer(string_packer);

		SetPacker<int8_t, 820> set_of_int8_packer(int8_packer);
		SetPacker<bool, 821> set_of_bool_packer(bool_packer);
		SetPacker<int16_t, 822> set_of_int16_packer(int16_packer);
		SetPacker<int32_t, 823> set_of_int32_packer(int32_packer);
		SetPacker<int64_t, 824> set_of_int64_packer(int64_packer);
		SetPacker<double, 825> set_of_float_packer(float_packer);
		SetPacker<string, 826> set_of_buffer_packer(buffer_packer);
		SetPacker<datetime, 827> set_of_date_packer(date_packer);
		SetPacker<string, 828> set_of_string_packer(string_packer);

		MapPacker<int32_t, int32_t, 850> map_of_int32_int32_packer(int32_packer, int32_packer);
		MapPacker<int32_t, string, 851> map_of_int32_string_packer(string_packer, int32_packer);
		MapPacker<string, int32_t, 852> map_of_string_int32_packer(int32_packer, string_packer);
		MapPacker<string, string, 853> map_of_string_string_packer(string_packer, string_packer);

	}
}
