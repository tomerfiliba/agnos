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

import sys
import traceback
import urlparse
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from .. import INFO_SERVICE, INFO_REFLECTION
from .xmlser import dumps as dump_xml, loads as load_xml
from .jsonser import dumps as dump_json, loads_root as load_json
from .util import import_file


ACCEPTED_FORMATS = dict(
    json = ("application/json", load_json, dump_json), 
    xml  = ("application/xml", load_xml, dump_xml),
)


class HttpError(Exception):
    def __init__(self, code, info, enc = "text/plain"):
        self.code = code
        self.info = info
        self.enc = enc


def get_dotted_attr(obj, dotted_name):
    parts = dotted_name.split(".")
    for p in parts:
        obj = getattr(obj, p)
    return obj


class RESTfulAgnosServer(object):
    def __init__(self, bindings_module, agnos_client):
        self.bindings_module = bindings_module
        self.client = agnos_client
        self.service_info = agnos_client.get_service_info(INFO_SERVICE)
        self.reflection = agnos_client.get_service_info(INFO_REFLECTION)
        self.func_map = {}
        self.proxy_map = {}
        for name, funcinfo in self.reflection["functions"].items():
            self.func_map[name] = get_dotted_attr(agnos_client, name)
            funcinfo["url"] = "/funcs/%s" % (name,)
    
    @classmethod
    def connect(cls, bindings_module, host, port):
        client = bindings_module.Client.connect(host, port)
        return cls(client)
    
    @classmethod
    def connect_executable(cls, bindings_module, executable, args = []):
        if isinstance(bindings_module, str):
            bindings_module = import_file(bindings_module)
        client = bindings_module.Client.connect_executable(executable, args)
        return cls(bindings_module, client)
    
    def start(self, host, port):
        class BoundRequestHandler(RequestHandler):
            root = self

        server = HTTPServer((host, port), BoundRequestHandler)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print ("Ctrl+C")
        finally:
            server.socket.close()


class RequestHandler(BaseHTTPRequestHandler):
    root = None

    #=========================================================================
    # GET
    #=========================================================================
    def _get_usage(self):
        pass
    
    def _get_root(self):
        return dict(info = "this is the RESTful server's root",
            service = dict(self.root.service_info),
            functions_url = "/funcs",
            objects_url = "/objs",
        )
    
    def _get_func(self, parts):
        if not len(parts):
            return self.root.func_map.keys()
        if len(parts) != 1:
            raise HttpError(404, "Invalud URL")
        name = parts[0]
        if name not in self.root.func_map:
            raise HttpError(404, "function does not exist")
        raise HttpError(405, "use POST to invoke function")

    def _get_obj(self, parts):
        if not parts:
            return self.root.proxy_map
        if len(parts) == 1:
            member = None
        elif len(parts) == 2:
            member = parts[1]
        else:
            raise HttpError(404, "Invalid URL")
        try:
            oid = int(parts[0])
        except ValueError:
            raise HttpError(404, "Invalid URL")
        if oid not in self.root.proxy_map:
            raise HttpError(404, "Invalid object ID")
        obj = self.root.proxy_map[oid]
        info = self.root.reflection["classes"][obj._idl_type]
        
        #print (info)
        
        if member:
            if member in info["attrs"] and info["attrs"][member]["get"]:
                return getattr(obj, member)
            else:
                raise HttpError(405, "use POST to invoke method or set attribute")
        
        info2 = dict(info.items())
        info2["class"] = obj._idl_type
        return info2
    
    def do_GET(self):
        try:
            code = 200
            url = urlparse.urlsplit(self.path)
            parts = [p.strip() for p in url.path.split("/") if p.strip()]
            params = dict(urlparse.parse_qsl(url.query))
            format = params.get("format", "json")
            if format not in ACCEPTED_FORMATS:
                raise HttpError(501, "Unsupported format")
            enc, _, dumper = ACCEPTED_FORMATS[format]
            
            if not parts:
                obj = self._get_root()
            elif parts[0] == "funcs":
                obj = self._get_func(parts[1:])
            elif parts[0] == "objs":
                obj = self._get_obj(parts[1:])
            else:
                raise HttpError(404, "Invalid URL")
            data = dumper(obj, self.root.proxy_map)
        except HttpError as ex:
            code = ex.code
            enc = ex.enc
            data = ex.info
            data += "\npath = " + self.path
        except Exception:
            code = 500
            enc = "text/plain"
            data = "".join(traceback.format_exception(*sys.exc_info()))
            data += "\npath = " + self.path
        
        self.send_response(code)
        self.send_header("Content-type", enc)
        self.send_header("Content-length", len(data))
        self.end_headers()
        self.wfile.write(data)
    
    #=========================================================================
    # POST
    #=========================================================================
    def _post_func(self, parts, kwargs):
        if len(parts) != 1:
            raise HttpError(404, "Invalud URL")
        name = parts[0]
        if name not in self.root.func_map:
            raise HttpError(404, "function does not exist")
        func = self.root.func_map[name]
        return func(**kwargs)

    def _post_obj(self, parts, kwargs):
        if len(parts) == 2:
            member = parts[1]
        else:
            raise HttpError(404, "Invalid URL")
        try:
            oid = int(parts[0])
        except ValueError:
            raise HttpError(404, "Invalid URL")
        if oid not in self.root.proxy_map:
            raise HttpError(404, "Invalid object ID")
        obj = self.root.proxy_map[oid]
        func = getattr(obj, member)
        return func(**kwargs)
    
    def do_POST(self):
        try:
            code = 200
            unslashed_path = "/".join(p for p in self.path.split("/") if p.strip())
            url = urlparse.urlsplit(unslashed_path)
            parts = [p.strip() for p in url.path.split("/") if p.strip()]

            params = dict(urlparse.parse_qsl(url.query))
            format = params.get("format", "json")
            if format not in ACCEPTED_FORMATS:
                raise HttpError(501, "Unsupported format")
            enc, loader, dumper = ACCEPTED_FORMATS[format]
            
            if "content-length" not in self.headers:
                raise HttpError(411, "content-length required")
            length = int(self.headers["content-length"])
            raw_payload = self.rfile.read(length).strip()
            if raw_payload:
                payload = loader(raw_payload, self.root.bindings_module, self.root.proxy_map)
            else:
                payload = {}
            
            if parts[0] == "funcs":
                obj = self._post_func(parts[1:], payload)
            elif parts[0] == "objs":
                obj = self._post_obj(parts[1:], payload)
            else:
                raise HttpError(404, "Invalid URL")
            data = dumper(obj, self.root.proxy_map)
        except HttpError as ex:
            code = ex.code
            enc = ex.enc
            data = ex.info
            data += "\npath = " + self.path
        except Exception:
            code = 500
            enc = "text/plain"
            data = "".join(traceback.format_exception(*sys.exc_info()))
            data += "\npath = " + self.path
        
        self.send_response(code)
        self.send_header("Content-type", enc)
        self.send_header("Content-length", len(data))
        self.end_headers()
        self.wfile.write(data)













