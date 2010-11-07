import sys
import time
from datetime import datetime
from base import TargetTest
from signal import SIGINT
from urllib import urlopen


class FeatureTestClient(TargetTest):
    def runTest(self):
        port = 8877
        self.proc = self.spawn([
            sys.executable, self.REL("libagnos/python/bin/restful-agnos"),
            "-p", str(port), 
            "-m", self.REL("tests/python-test/FeatureTest_bindings.py"), 
            "--exec", "%s %s -m lib" % (sys.executable, self.REL("tests/python-test/server.py")),
            ])
        time.sleep(1)
        if self.proc.poll() is not None:
            print "server stdout: ", self.proc.stdout.read()
            print "server stderr: ", self.proc.stderr.read()
            self.fail("restful webserver failed to start")
        
        try:
            self.baseurl = "http://localhost:%s" % (port,)
            self.client()
            print "===== success ======"
        finally:
            self.proc.send_signal(SIGINT)
            self.proc.wait()
    
    def _request(self, path, data, format, retcodes = [200]):
        if not data:
            data = "    "
        url = self.baseurl + "/" + path + "?format=" + format
        f = urlopen(url, data)
        rc = f.getcode()
        data = f.read()
        if rc not in retcodes:
            print data
            self.fail("got HTTP code %s" % (f.getcode(),))
        return data
    
    def _query(self, path, format, retcodes = [200]):
        f = urlopen(self.baseurl + "/" + path + "?format=" + format)
        rc = f.getcode()
        data = f.read()
        if rc not in retcodes:
            print data
            self.fail("got HTTP code %s" % (f.getcode(),))
        return data
    
    def xml_request(self, path, data = None, retcodes = [200]):
        return self._request(path, data, "xml", retcodes)

    def json_request(self, path, data = None, retcodes = [200]):
        return self._request(path, data, "json", retcodes)

    def xml_query(self, path, retcodes = [200]):
        return self._query(path, "xml", retcodes)

    def json_query(self, path, retcodes = [200]):
        return self._query(path, "json", retcodes)
    
    def client(self):
        print self.xml_request("funcs/get_class_c")
        print
        print self.xml_query("objs")
        print
        print self.json_request("funcs/get_class_c")
        print
        print self.json_query("objs")
        



if __name__ == "__main__":
    import unittest
    unittest.main()

    import sys
    
    sys.argv = [sys.argv[0], ]

