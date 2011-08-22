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
if __package__ is None:
    import agnos.restful #@UnusedImport
    __package__ = "agnos.restful"

import base64
import json
import agnos
from datetime import datetime
from .util import iso_to_datetime, long, basestring, url_to_proxy


#===============================================================================
# dumping
#===============================================================================
def _dump(obj, proxy_map):
    if obj is None:
        return obj
    elif isinstance(obj, bool):
        return obj
    elif isinstance(obj, (int, long)):
        return obj
    elif isinstance(obj, float):
        return obj
    elif isinstance(obj, basestring):
        return str(obj)
    elif isinstance(obj, bytes):
        return dict(type = "buffer", value = base64.b64encode(obj).decode("utf8"))
    elif isinstance(obj, datetime):
        return dict(type = "datetime", value = obj.isoformat()) 
    elif isinstance(obj, (list, tuple)):
        return [_dump(item, proxy_map) for item in obj]
    elif isinstance(obj, (set, frozenset)):
        return dict(type = "set", value = [_dump(item, proxy_map) for item in obj])
    elif isinstance(obj, dict):
        return dict(type = "map", 
            value = [(_dump(k, proxy_map), _dump(v, proxy_map)) 
                for k, v in obj.items()])
    elif isinstance(obj, agnos.HeteroMap):
        return dict(type = "heteromap", 
            value = [(_dump(k, proxy_map), _dump(v, proxy_map)) 
                for k, v in obj.items()])
    # enums
    elif isinstance(obj, agnos.Enum):
        return dict(type = "enum", name = obj._idl_type, member = obj.name)
    # records
    elif isinstance(obj, agnos.BaseRecord):
        return dict(type = "record", name = obj._idl_type, 
            value = dict((name, _dump(getattr(obj, name), proxy_map))
                for name in obj._idl_attrs))
    # proxies
    elif isinstance(obj, agnos.BaseProxy):
        proxy_map[obj._objref] = obj
        return dict(type = "proxy", name = obj._idl_type, url = "/objs/%s" % (obj._objref,))
    else:
        raise TypeError("cannot dump %r" % (type(obj),))

def dumps(obj, proxy_map):
    simplified = _dump(obj, proxy_map)
    return json.dumps(simplified)


#===============================================================================
# loading
#===============================================================================
def _load(obj, bindings_module, proxy_map):
    if isinstance(obj, (type(None), bool, int, float, long, basestring)):
        return obj
    elif isinstance(obj, list):
        return [_load(item, bindings_module, proxy_map) for item in obj]
    elif not isinstance(obj, dict):
        raise TypeError("cannot load %r" % (obj,))
    
    # it's a dict
    if "type" not in obj:
        raise ValueError("malformed: %r" % (obj,))
    if obj["type"] == "buffer":
        return base64.b64decode(obj["value"].encode("utf8"))
    elif obj["type"] == "datetime":
        return iso_to_datetime(obj["value"])
    elif obj["type"] == "set":
        return set(_load(item, bindings_module, proxy_map) for item in obj["value"])
    elif obj["type"] == "map":
        return dict((_load(k, bindings_module, proxy_map), _load(v, bindings_module, proxy_map)) 
            for k, v in obj["value"])
    elif obj["type"] == "heteromap":
        hmap = agnos.HeteroMap()
        for k, v in obj["value"]:
            kk = _load(k, bindings_module, proxy_map)
            vv = _load(v, bindings_module, proxy_map)
            hmap[kk] = vv 
        return hmap
    elif obj["type"] == "enum":
        enum_cls = getattr(bindings_module, obj["name"])
        return getattr(enum_cls, obj["member"])
    elif obj["type"] == "record":
        rec_cls = getattr(bindings_module, obj["name"])
        rec = rec_cls()
        for name, child in obj["value"].items():
            val = _load(child, bindings_module, proxy_map)
            setattr(rec, name, val)
        return rec
    elif obj["type"] == "proxy":
        return url_to_proxy(obj["url"], proxy_map)
    else:
        raise TypeError("invalid type %r" % (obj["type"],))


def loads(data, bindings_module, proxy_map):
    jsonobj = json.loads(data)
    return _load(jsonobj, bindings_module, proxy_map)

def loads_root(data, bindings_module, proxy_map):
    jsonobj = json.loads(data)
    return dict((k, _load(v, bindings_module, proxy_map)) 
        for k, v in jsonobj.items())


if __name__ == "__main__":
    from agnos.utils import create_enum
    import FeatureTest_bindings
    
    FeatureTest_bindings.moshe = create_enum("moshe", dict(a=1,b=2,c=3))
    x = FeatureTest_bindings.RecordB(1,2,3)
    p = FeatureTest_bindings.PersonProxy(x, 1234, False)
    
    h = agnos.HeteroMap()
    h["foo"] = 17
    h["bar"] = None
    h[19] = 3.1415926
       
    obj = [set([18,19,True,4.25]), datetime.now(), {"foo" : 1, "bar" : 2},
        FeatureTest_bindings.moshe.a, x, p, h]
    text = dumps(obj, {p : 1234})
    print text
    obj2 = loads(text, FeatureTest_bindings, {1234 : p})
    print obj
    print obj2
    assert obj == obj2



















