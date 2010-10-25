import urllib2
import json

args = {}
req = urllib2.Request("http://localhost:8088/funcs/get_class_c", json.dumps(args))
req.add_header("Content-type", "application/json")

print urllib2.urlopen(req).read()

