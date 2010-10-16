import os
import signal
import unittest
import time
from base import TargetTest


class TestJava(TargetTest):
    def runTest(self):
        self.run_agnosc("java", "tests/features.xml", "tests/java-test/bindings")
        print "scons"
        self.run_cmdline("scons", cwd = self.REL("tests/java-test"))
        
        print "./myserver -m lib"
        serverproc = self.spawn(["./myserver.sh", "-m", "lib"], cwd = self.REL("tests/java-test"))
        time.sleep(1)
        if serverproc.poll() is not None:
            print "server stdout: ", serverproc.stdout.read()
            print "server stderr: ", serverproc.stderr.read()
            self.fail("server failed to start")

        try:
            banner = serverproc.stdout.readline().strip()
            self.failUnless(banner == "AGNOS", banner)
            host = serverproc.stdout.readline().strip()
            port = serverproc.stdout.readline().strip()
            print "./myclient", host, port
            clientproc = self.spawn(["./myclient.sh", host, port], cwd = self.REL("tests/java-test"))
    
            print "===client output==="
            print clientproc.stdout.read()
            print clientproc.stderr.read()
            print "==================="
            self.assertTrue(clientproc.wait() == 0)
        finally:
            serverproc.send_signal(signal.SIGINT)
            time.sleep(1)
            try:
                if serverproc.poll() is None:
                    serverproc.kill()
            except Exception:
                pass
            print "===server output==="
            print serverproc.stdout.read()
            print serverproc.stderr.read()
            print "==================="


if __name__ == '__main__':
    unittest.main()


