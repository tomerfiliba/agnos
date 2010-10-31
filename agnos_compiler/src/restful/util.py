import os
from types import ModuleType
from .iso8601 import parse_date as iso_to_date


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


def import_file(filename, name = None, package = None):
    if name is None:
        name = os.path.basename(name).split(".")[0]
    mod = ModuleType()
    if package is not None:
        mod.__path__ = package
    execfile(filename, mod.__dict__)
    return mod


