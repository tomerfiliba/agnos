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

import sys
import traceback
import agnos
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer


class HttpError(Exception):
    def __init__(self, code, info):
        self.code = code
        self.info = info


def get_dotted_attr(obj, dotted_name):
    parts = dotted_name.split(".")
    for p in parts:
        obj = getattr(obj, p)
    return obj


class RESTfulAgnosServer(object):
    def __init__(self, agnos_client):
        self.client = agnos_client
        self.types = agnos_client.get_service_info(agnos.INFO_TYPES)
        self.service = agnos_client.get_service_info(agnos.INFO_SERVICE)
        self.func_map = {}
        self.proxy_map = {}
        for name, funcinfo in client_service["functions"].iteritems():
            func_map[name] = get_dotted_attr(agnos_client, name)
            funcinfo["url"] = "/funcs/%s" % (name,)
    
    @classmethod
    def connect(cls, bindings_module, host, port):
        client = bindings_module.Client.connect(host, port)
        return cls(client)
    
    @classmethod
    def connect_executable(cls, bindings_module, executable, args = []):
        client = bindings_module.Client.connect_executable(executable, args)
        return cls(client)
    
    def start(self, host, port):
        class BoundRequestHandler(RequestHandler):
            root = self

        server = HTTPServer((host, port), BoundRequestHandler)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print "Ctrl+C"
        finally:
            server.socket.close()


class RequestHandler(BaseHTTPRequestHandler):
    root = None

    #=========================================================================
    # GET
    #=========================================================================
    def _get_usage(self):
        data = """
        <html><head>
        <title>RESTful Agnos Protocol</title>
        </head><body>
        <h1>Greetings, Human</h1>
        <p>
        The <a href="http://agnos.sourceforge.net">Agnos</a> binary protocol
        (<code>libagnos</code>) has not been implememted for every programming
        language. If you need to use an Agnos service from a language that
        <code>libagnos</code> does not support, you can use this <b>RESTful API</b>.
        This webserver exposes the Agnos service through the use of reflection,
        meaning the webserver itself is "dumb" -- it simply maps functions
        and objects to URLs, so using them would be easy.
        </p>
        <p>
        You can use the RESTful API through two serialization schemes: 
        <a href="/json">JSON</a> and <a href="/xml">XML</a>.
        </p>
        <p>
        For usage instructions, see the
        <a href="http://agnos.sourceforge.net/restful.html">reference</a>.
        </p>
        </body></html>"""
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.send_header("Content-length", len(data))
        self.end_headers()
        self.wfile.write(data)
        
    
    
    def _get_root(self):
        return self.root.service
    
    def _get_func(self, path):
        if path not in self.root.func_map:
            raise HttpError(404, "function does not exist")
        raise HttpError(405, "use POST to invoke function")

    def _get_obj(self, path):
        obj, member = parse_obj_url(path)
        clsname = type(obj).__name__[:-5]
        info = client_types["classes"][clsname]
        info2 = dict(info.iteritems())
        info2["class"] = clsname

        if member:
            raise HttpError(405, "use POST to invoke function")
        
        return info2
    
    def do_GET(self):
        try:
            code = 200
            if self.path.strip("/") == "":
                obj = self._get_root()
            elif self.path.startswith("/funcs/"):
                obj = self._get_func(self.path[7:])
            elif self.path.startswith("/objs/"):
                obj = self._get_obj(self.path[6:])
            else:
                raise HttpError(404, "Invalid URL")
        except HttpError, ex:
            code = ex.code
            obj = ex.info
        except Exception:
            code = 500
            obj = "".join(traceback.format_exception(*sys.exc_info()))
        
        print "!!", repr(obj)
        
        self.send_response(code)
        data = json.dumps(obj, cls = AgnosJSONEncoder)
        self.send_header("Content-type", "application/json")
        self.send_header("Content-length", len(data))
        self.end_headers()
        self.wfile.write(data)
        
    #=========================================================================
    # POST
    #=========================================================================
    def _post_func(self, path, payload):
        if path not in func_map:
            raise HttpError(404, "function does not exist")
        return self.root.func_map[path](**payload)

    def _post_obj(self, path, payload):
        obj, member = self.parse_obj_url(path)
        clsname = type(obj).__name__[:-5]
        info = client_types["classes"][clsname]
        if member in info["methods"]:
            method = getattr(obj, member)
            return method(**payload)
        elif member in info["attrs"]:
            setattr(obj, member, payload)
        else:
            HttpError(404, "invalid method or attribute name")
    
    def do_POST(self):
        mode = "json"
        try:
            if "Content-length" not in self.headers:
                raise HttpError(411, "Content-length required")
            if "Content-type" not in self.headers:
                raise HttpError(406, "Content-type must be 'application/json' or 'application/xml'")
            if self.headers["Content-type"] == "application/json":
                mode = "json"
            elif self.headers["Content-type"] in ("application/xml", "text/xml"):
                mode = "xml"
            else:
                raise HttpError(406, "Content-type must be 'application/json' or 'application/xml'")
            
            code = 200
            length = int(self.headers["Content-length"])
            raw_payload = self.rfile.read(length)
            if not raw_payload:
                payload = None
            elif mode == "json":
                payload = json.loads(raw_payload, object_hook = agnos_json_decoder)
            elif mode == "xml":
                payload = xml_loads(raw_payload)
            else:
                assert False, "invalid mode"
            
            if self.path.startswith("/funcs/"):
                obj = self._post_func(self.path[7:], payload)
            elif self.path.startswith("/objs/"):
                obj = self._post_obj(self.path[6:], payload)
            else:
                raise HttpError(404, "Invalid URL")
        except HttpError, ex:
            code = ex.code
            obj = ex.info
        except Exception:
            code = 500
            obj = "".join(traceback.format_exception(*sys.exc_info()))

        print "!!", repr(obj)
        
        if mode == "json":
            data = json.dumps(obj, cls = AgnosJSONEncoder)
        elif mode == "xml":
            data = xml_dumps(obj)
        else:
            assert False, "invalid mode"
        
        self.send_response(code)
        self.send_header("Content-type", "application/json")
        self.send_header("Content-length", len(data))
        self.end_headers()
        self.wfile.write(data)

