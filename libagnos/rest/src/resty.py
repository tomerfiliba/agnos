import urlparse
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
import agnos
import sys
import traceback
import json
from agnos_compiler.langs.xml import XmlDoc
from agnos.utils import HeteroMap
import FeatureTest_bindings


agnos_client = FeatureTest_bindings.Client.connect_executable("python", ["server.py", "-m", "lib"])
client_functions = agnos_client.get_service_info(agnos.INFO_FUNCTIONS)
client_types = agnos_client.get_service_info(agnos.INFO_TYPES)
client_service = agnos_client.get_service_info(agnos.INFO_SERVICE)

func_map = {}
proxy_map = {}

def get_dotted_attr(obj, dotted_name):
    parts = dotted_name.split(".")
    for p in parts:
        obj = getattr(obj, p)
    return obj

for name, funcinfo in client_service["functions"].iteritems():
    func_map[name] = get_dotted_attr(agnos_client, name)
    funcinfo["url"] = "/funcs/%s" % (name,)

def parse_obj_url(path):
    if "/" in path:
        oid, member = path.split("/", 1)
    else:
        member = None
        oid = path
    try:
        oid = int(oid)
    except ValueError:
        raise HttpError(404, "invalid object id")
    if oid not in proxy_map:
        raise HttpError(404, "object id does not exist")
    obj = proxy_map[oid]
    return obj, member


class AgnosJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        # heteromaps
        if isinstance(obj, HeteroMap):
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


class HttpError(Exception):
    def __init__(self, code, info):
        self.code = code
        self.info = info


class AgnosRESTfulHandler(BaseHTTPRequestHandler):
    #=========================================================================
    # GET
    #=========================================================================
    def _get_root(self):
        return client_service
    
    def _get_func(self, path):
        if path not in func_map:
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
        return func_map[path](**payload)

    def _post_obj(self, path, payload):
        obj, member = parse_obj_url(path)
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
        try:
            if "Content-length" not in self.headers:
                raise HttpError(411, "Content-length required")
            if self.headers.get("Content-type", None) != "application/json":
                raise HttpError(406, "Content-type must be application/json")
            code = 200
            length = int(self.headers["Content-length"])
            raw_payload = self.rfile.read(length)
            if not raw_payload:
                raw_payload = "null"
            if self.path.startswith("/funcs/"):
                payload = json.loads(raw_payload, object_hook = agnos_json_decoder)
                obj = self._post_func(self.path[7:], payload)
            elif self.path.startswith("/objs/"):
                payload = json.loads(raw_payload, object_hook = agnos_json_decoder)
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
        
        self.send_response(code)
        data = json.dumps(obj, cls = AgnosJSONEncoder)
        self.send_header("Content-type", "application/json")
        self.send_header("Content-length", len(data))
        self.end_headers()
        self.wfile.write(data)



def main(host = "0.0.0.0", port = 8088):
    server = HTTPServer((host, port), AgnosRESTfulHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.socket.close()

if __name__ == "__main__":
    main()

