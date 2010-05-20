import sys
import os
import signal
import unittest
import time
from base import TargetTest


class TestJava(TargetTest):
    def run_msbuild(self, sln):
        print "msbuild", sln
        if sys.platform == "win32":
            # assume .net
            self.run_cmdline([r"C:\Windows\Microsoft.NET\Framework\v3.5\MSBuild.exe", sln])
        else: 
            # assume mono
            self.run_cmdline([r"xbuild", sln])
    
    def runTest(self):
        self.run_agnosc("c#", "ut2/RemoteFiles.xml", "ut2/gen-csharp")
        self.run_msbuild("ut2/csharp/agnostest.sln")


if __name__ == '__main__':
    unittest.main()


