import os
import signal
import unittest
import time
from base import TargetTest


class TestPython(TargetTest):
    def run_python(self, file, pythonpath):
        return self.spawn(["python", file])
    
    def runTest(self):
        self.run_agnosc("python", "ut2/RemoteFiles.xml", "ut2/gen-python")
        serverproc = self.run_python("ut2/python/myserver.py", ["ut2/gen-python"])
        time.sleep(1)
        clientproc = self.run_python("ut2/python/myclient.py", ["ut2/gen-python"])
        #self.assertTrue(clientproc.wait() == 0)
        print "===client output==="
        print clientproc.stdout.read()
        print clientproc.stderr.read()
        print "==================="
        serverproc.send_signal(signal.SIGINT)
        self.assertTrue(serverproc.wait() == 0)



if __name__ == '__main__':
    unittest.main()


