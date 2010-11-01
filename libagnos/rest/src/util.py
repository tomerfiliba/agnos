import os
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
    parts = [part.strip() for part in url.split("/") if part.strip()]
    if len(parts) != 3 or part[0] not in ("xml", "json") or part[1] != "objs":
        raise ValueError("invalid proxy url: %r" % (url,))
    try:
        oid = int(parts[2])
    except ValueError:
        raise ValueError("invalid proxy url: %r" % (url,))
    try:
        return proxy_map[oid]
    except KeyError:
        raise ValueError("nonexisting objref: %r" % (url,))


# Yoinked from python docs
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

#
# references:
#     http://code.google.com/p/pyiso8601/
#     http://www.w3.org/TR/NOTE-datetime, 
#     http://en.wikipedia.org/wiki/ISO_8601
#
def iso_to_date(text):
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
        

def import_file(filename, name = None, package = None):
    if name is None:
        name = os.path.basename(name).split(".")[0]
    mod = ModuleType()
    if package is not None:
        mod.__path__ = package
    execfile(filename, mod.__dict__)
    return mod



if __name__ == "__main__":
    print iso_to_date("19970716")
    print iso_to_date("1997-07-16")
    print iso_to_date("19970716T19:20")
    print iso_to_date("1997-07-16T19:20")
    print iso_to_date("19970716T19:20Z")
    print iso_to_date("1997-07-16T19:20+01:30")
    print iso_to_date("1997-07-16T19:20-01:30")
    print iso_to_date("1997-07-16T19:20:30")
    print iso_to_date("1997-07-16T19:20:30.45")
    print iso_to_date("1997-07-16T19:20:30.45Z")
    print iso_to_date("1997-07-16T19:20:30.45+01:30")
    print iso_to_date("1997-07-16T19:20:30.45-01:30")

