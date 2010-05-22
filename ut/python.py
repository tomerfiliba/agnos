import os
import signal
import unittest
import time
from base import TargetTest


class TestPython(TargetTest):
    def run_python(self, file, pythonpath):
        return self.spawn(["python", file])
    
    def runTest(self):
        self.run_agnosc("python", "ut/RemoteFiles.xml", "ut/gen-python")
        serverproc = self.run_python("ut/python/myserver.py", ["ut/gen-python"])
        time.sleep(1)
        clientproc = self.run_python("ut/python/myclient.py", ["ut/gen-python"])
        #self.assertTrue(clientproc.wait() == 0)
        print "===client output==="
        print clientproc.stdout.read()
        print clientproc.stderr.read()
        print "==================="
        serverproc.send_signal(signal.SIGINT)
        self.assertTrue(serverproc.wait() == 0)



if __name__ == '__main__':
    unittest.main()


