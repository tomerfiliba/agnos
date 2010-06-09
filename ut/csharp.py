import os
import signal
import unittest
import time
from base import TargetTest


class TestCSharp(TargetTest):
    def run_msbuild(self, sln):
        print "msbuild", sln
        if sys.platform == "win32":
            # assume .net
            self.run_cmdline([r"C:\Windows\Microsoft.NET\Framework\v3.5\MSBuild.exe", sln])
        else: 
            # assume mono
            self.run_cmdline([r"xbuild", sln])
    
    def find_exe(self, path):
        progs = []
        for root, dirs, files in os.walk(path):
            for fn in files:
                if fn.endswith(".exe"):
                    progs.append(os.path.join(root, fn)) 
        return progs
    
    def runTest(self):
        self.run_agnosc("c#", "ut/features.xml", "ut/gen-csharp")
        
        return
        
        self.run_msbuild("ut/csharp-test/agnostest.sln")
        server_exe = self.find_exe("ut/csharp-test/server/bin")
        client_exe = self.find_exe("ut/csharp-test/client/bin")

        self.assertTrue(len(server_exe) == 1)
        server_exe = server_exe[0]
        self.assertTrue(len(client_exe) == 1)
        client_exe = client_exe[0]
        print "server_exe:", server_exe
        print "client_exe:", client_exe
        
        return

        try:
            serverproc = self.spawn(server_exe)
            time.sleep(1)
            clientproc = self.spawn(client_exe)
            print "===client output==="
            print clientproc.stdout.read()
            print clientproc.stderr.read()
            print "==================="
            self.assertTrue(clientproc.wait() == 0)
            serverproc.send_signal(signal.SIGINT)
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


