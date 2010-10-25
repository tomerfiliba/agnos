##############################################################################
# Part of the Agnos RPC Framework
#    http://agnos.sourceforge.net
#
# Copyright 2010, Tomer Filiba (tomerf@il.ibm.com; tomerfiliba@gmail.com)
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
import json


class AgnosJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        # heteromaps
        if isinstance(obj, agnos.HeteroMap):
            dct = dict(obj.iteritems())
            dct["__heteromap__"] = "HeteroMap"
            return dct
        # proxies
        elif isinstance(obj, agnos.BaseProxy):
            proxy_map[obj._objref] = obj
            return {"__proxy__" : type(obj).__name__[:-5], "url" : "/objs/%s" % (obj._objref,)}
        # records
        elif hasattr(obj, "_recid") and hasattr(obj, "_ATTRS"):
            dct = dict((name, getattr(obj, name)) for name in obj._ATTRS)
            dct["__record__"] = type(obj).__name__
            return dct
        else:
            return json.JSONEncoder.default(self, obj)

def agnos_json_decoder(dct):
    # convert url to object
    if "__proxy__" in dct:
        obj, member = parse_obj_url("url")
        if not member:
            return obj
        else:
            return None
    # records to objects
    # heteromaps to objects
    else:
        return dct
