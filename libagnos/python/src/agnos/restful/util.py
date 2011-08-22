##############################################################################
# Part of the Agnos RPC Framework
#    http://agnos.sourceforge.net
#
# Copyright 2011, International Business Machines Corp.
#                 Author: Tomer Filiba (tomerf@il.ibm.com)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
##############################################################################

"""
#>>> mod = import_file("./some_file.py")
#>>> print mod    #doctest: +ELLIPSIS
#<module 'FeatureTest_bindings' from ...>

>>> print iso_to_datetime("19970716")
1997-07-16 00:00:00
>>> print iso_to_datetime("1997-07-16")
1997-07-16 00:00:00
>>> print iso_to_datetime("19970716T19:20")
1997-07-16 19:20:00
>>> print iso_to_datetime("1997-07-16T19:20")
1997-07-16 19:20:00
>>> print iso_to_datetime("19970716T19:20Z")
1997-07-16 19:20:00+00:00
>>> print iso_to_datetime("1997-07-16T19:20+01:30")
1997-07-16 19:20:00+01:30
>>> print iso_to_datetime("1997-07-16T19:20-01:30")
1997-07-16 19:20:00-01:30
>>> print iso_to_datetime("1997-07-16T19:20:30")
1997-07-16 19:20:30
>>> print iso_to_datetime("1997-07-16T19:20:30.45")
1997-07-16 19:20:30.450000
>>> print iso_to_datetime("1997-07-16T19:20:30.45Z")
1997-07-16 19:20:30.450000+00:00
>>> print iso_to_datetime("1997-07-16T19:20:30.45+01:30")
1997-07-16 19:20:30.450000+01:30
>>> print iso_to_datetime("1997-07-16T19:20:30.45-01:30")
1997-07-16 19:20:30.450000-01:30
"""

import os
import sys
from types import ModuleType
from datetime import datetime, timedelta, tzinfo


try:
    basestring = basestring
except NameError:
    basestring = str
try:
    long = long
except NameError:
    long = type(None)


def url_to_proxy(url, proxy_map):
    parts = [str(part.strip()) for part in url.split("/") if part.strip()]
    if len(parts) != 2 or parts[0] != "objs":
        raise ValueError("invalid proxy url: %r" % (url,))
    try:
        oid = int(parts[1])
    except ValueError:
        raise ValueError("invalid proxy url: %r" % (url,))
    try:
        return proxy_map[oid]
    except KeyError:
        raise ValueError("nonexisting objref: %r" % (url,))


#
# references:
#     http://code.google.com/p/pyiso8601/
#     http://www.w3.org/TR/NOTE-datetime, 
#     http://en.wikipedia.org/wiki/ISO_8601
#
class _UTC(tzinfo):
    def utcoffset(self, dt):
        return timedelta(0)
    def tzname(self, dt):
        return "UTC"
    def dst(self, dt):
        return timedelta(0)
UTC = _UTC()

class FixedOffset(tzinfo):
    """Fixed offset in hours and minutes from UTC"""
    def __init__(self, hours, minutes):
        self._offset = timedelta(hours=hours, minutes=minutes)
        if hours < 0:
            self._name = "-%02d:%02d" % (abs(hours), abs(minutes))
        else:
            self._name = "+%02d:%02d" % (hours, minutes)
    def utcoffset(self, dt):
        return self._offset
    def tzname(self, dt):
        return self._name
    def dst(self, dt):
        return timedelta(0)
    def __repr__(self):
        return "<FixedOffset %r>" % (self._name,)

def iso_to_datetime(text):
    if "T" in text:
        d, t = text.split("T")
    else:
        d = text
        t = None
    if "-" in d:
        year, month, day = d.split("-")
    else:
        year = d[0:4]
        month = d[4:6]
        day = d[6:8]
    if not t:
        return datetime(int(year), int(month), int(day))
    if "Z" in t:
        t = t.split("Z")[0]
        tz = UTC
    elif "+" in t:
        t, tz = t.split("+")
        h, m = tz.split(":")
        tz = FixedOffset(int(h), int(m))
    elif "-" in t:
        t, tz = t.split("-")
        h, m = tz.split(":")
        tz = FixedOffset(-int(h), -int(m))
    else:
        tz = None # local time
    parts = t.split(":")
    if len(parts) == 2:
        hour = parts[0]
        minute = parts[1]
        second = "0"
    else:
        hour = parts[0]
        minute = parts[1]
        second = parts[2]
    if "." in second:
        second, frac = second.split(".")
        frac = "0." + frac
    else:
        frac = 0
    return datetime(int(year), int(month), int(day), int(hour), int(minute), 
        int(second), int(float(frac) * 1000000), tz)


def import_file(filename, name = None, package = None, add_to_sys_modules = False):
    if os.path.isdir(filename):
        filename = os.path.join(filename, "__init__.py")
    if name is None:
        name = os.path.basename(filename).split(".")[0]
        dirname = os.path.basename(os.path.dirname(filename)).strip()
        if name == "__init__" and dirname:
            name = dirname
        elif package is not None:
            name = package + "." + name
    mod = ModuleType(name)
    mod.__file__ = os.path.abspath(filename)
    if package is not None:
        mod.__package__ = package
        mod.__path__ = [os.path.dirname(mod.__file__)]
    if add_to_sys_modules:
        sys.modules[name] = mod
    execfile(filename, mod.__dict__)
    return mod



if __name__ == "__main__":
    import doctest
    doctest.testmod()







