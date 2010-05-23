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

        try:
            serverproc = self.run_python("ut/python-test/myserver.py", ["ut/gen-python"])
            time.sleep(1)
            clientproc = self.run_python("ut/python-test/myclient.py", ["ut/gen-python"])
            #self.assertTrue(clientproc.wait() == 0)
            print "===client output==="
            print clientproc.stdout.read()
            print clientproc.stderr.read()
            print "==================="
            self.assertTrue(clientproc.wait() == 0)
            serverproc.send_signal(signal.SIGINT)
            #self.assertTrue(serverproc.wait() == 0)
            serverproc.wait()
        finally:
            try:
                clientproc.kill()
            except Exception:
                pass
            try:
                serverproc.kill()
            except Exception:
                pass


if __name__ == '__main__':
    unittest.main()


