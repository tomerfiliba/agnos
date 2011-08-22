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

import agnos
import base64
from datetime import datetime
from agnos_compiler.langs.xml import XmlDoc
import xml.etree.ElementTree as etree
from .util import iso_to_datetime, long, basestring, url_to_proxy


#===============================================================================
# dumping
#===============================================================================
def _dump(obj, doc, proxy_map):
    if obj is None:
        doc.elem("null")
    elif isinstance(obj, bool):
        doc.elem("true" if obj else "false")
    elif isinstance(obj, (int, long)):
        doc.elem("int", value = str(obj))
    elif isinstance(obj, float):
        doc.elem("float", value = str(obj))
    elif isinstance(obj, basestring):
        doc.elem("str", value = str(obj))
    elif isinstance(obj, bytes):
        doc.elem("buffer", value = base64.b64encode(obj).decode("utf8"))
    elif isinstance(obj, datetime):
        doc.elem("date", value = obj.isoformat())
    elif isinstance(obj, (list, tuple)):
        with doc.block("list"):
            for item in obj:
                _dump(item, doc, proxy_map)
    elif isinstance(obj, (set, frozenset)):
        with doc.block("set"):
            for item in obj:
                _dump(item, doc, proxy_map)
    elif isinstance(obj, dict):
        with doc.block("map"):
            for k, v in obj.items():
                with doc.block("item"):
                    with doc.block("key"):
                        _dump(k, doc, proxy_map)
                    with doc.block("value"):
                        _dump(v, doc, proxy_map)
    elif isinstance(obj, agnos.HeteroMap):
        with doc.block("heteromap"):
            for k, v in obj.items():
                with doc.block("item"):
                    with doc.block("key"):
                        _dump(k, doc, proxy_map)
                    with doc.block("value"):
                        _dump(v, doc, proxy_map)
    # enums
    elif isinstance(obj, agnos.Enum):
        doc.elem("enum", type = obj._idl_type, member = obj.name)
    # records
    elif isinstance(obj, agnos.BaseRecord):
        with doc.block("record"):
            doc.attr(type = obj._idl_type)
            for name in obj._idl_attrs:
                with doc.block("attr", name = name):
                    _dump(getattr(obj, name), doc, proxy_map)
    # proxies
    elif isinstance(obj, agnos.BaseProxy):
        proxy_map[obj._objref] = obj
        with doc.block("proxy"):
            doc.attr(type = obj._idl_type)
            doc.attr(url = "/objs/%s" % (obj._objref,))
    else:
        raise TypeError("cannot dump %r" % (type(obj),))


def dump_to_xml(obj, proxy_map):
    doc = XmlDoc("fake-root")
    _dump(obj, doc, proxy_map)
    doc.tag = doc.children[0].tag
    doc.attrs = doc.children[0].attrs
    doc.children = doc.children[0].children
    return doc

def dumps(obj, proxy_map, lean = True):
    doc = dump_to_xml(obj, proxy_map)
    return doc.render(lean)


#===============================================================================
# loading
#===============================================================================
def _load(elem, bindings_module, proxy_map):
    if elem.tag == "null":
        return None
    elif elem.tag == "true":
        return True
    elif elem.tag == "false":
        return False
    elif elem.tag == "int":
        return int(elem.attrib["value"])
    elif elem.tag == "float":
        return float(elem.attrib["value"])
    elif elem.tag == "str":
        return str(elem.attrib["value"])
    elif elem.tag == "buffer":
        return bytes(elem.attrib["value"])
    elif elem.tag == "date":
        return iso_to_datetime(elem.attrib["value"])
    elif elem.tag == "list":
        return [_load(child, bindings_module, proxy_map) 
            for child in elem.getchildren()]
    elif elem.tag == "set":
        return set(_load(child, bindings_module, proxy_map) 
            for child in elem.getchildren())
    elif elem.tag == "map":
        map = {}
        for child in elem.getchildren():
            k = _load(child.find("key").getchildren()[0], bindings_module, proxy_map)
            v = _load(child.find("value").getchildren()[0], bindings_module, proxy_map)
            map[k] = v
        return map
    elif elem.tag == "heteromap":
        hmap = agnos.HeteroMap()
        for child in elem.getchildren():
            k = _load(child.find("key").getchildren()[0], bindings_module, proxy_map)
            v = _load(child.find("value").getchildren()[0], bindings_module, proxy_map)
            hmap[k] = v
        return hmap
    elif elem.tag == "enum":
        enum_cls = getattr(bindings_module, elem.attrib["type"])
        return getattr(enum_cls, elem.attrib["member"])
    elif elem.tag == "record":
        rec_cls = getattr(bindings_module, elem.attrib["type"])
        rec = rec_cls()
        for child in elem.getchildren():
            name = child.attrib["name"]
            val = _load(child.getchildren()[0], bindings_module, proxy_map)
            setattr(rec, name, val)
        return rec
    elif elem.tag == "proxy":
        return url_to_proxy(elem.attrib["url"], proxy_map)
    else:
        raise ValueError("cannot load %r" % (elem.tag,))

            
def loads(data, bindings_module, proxy_map):
    xml = etree.fromstring(data)
    return _load(xml, bindings_module, proxy_map)


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






