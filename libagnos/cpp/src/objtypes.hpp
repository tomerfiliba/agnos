#ifndef AGNOS_OBJTYPES_HPP_INCLUDED
#define AGNOS_OBJTYPES_HPP_INCLUDED

#include <stddef.h>

#include <string>
#include <vector>
#include <map>
#include <set>
#include <utility>

#include <boost/any.hpp>
#include <boost/variant.hpp>
#include <boost/shared_ptr.hpp>
#include <boost/weak_ptr.hpp>
#include <boost/bind.hpp>
#include <boost/scoped_ptr.hpp>
//#include <boost/foreach.hpp>
#include <boost/date_time.hpp>
#include <boost/utility.hpp>


#ifdef _MSC_VER
typedef __int8 int8_t;
typedef __int16 int16_t;
typedef __int32 int32_t;
typedef __int64 int64_t;
#else
#include <stdint.h>
#endif

namespace agnos
{
	using std::string;
	using std::vector;
	using std::map;
	using std::set;

	using boost::any;
	using boost::shared_ptr;
	using boost::weak_ptr;
	using boost::scoped_ptr;
	using boost::any_cast;
	using boost::variant;

	typedef boost::posix_time::ptime datetime;
	typedef boost::posix_time::time_duration timespan;

	typedef int64_t objref_t;

}


#endif // AGNOS_OBJTYPES_HPP_INCLUDED
