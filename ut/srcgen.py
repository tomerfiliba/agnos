import os
import signal
import unittest
import time
from base import TargetTest


class TestPython(TargetTest):
    def run_srcgen(self, path, outdir):
        self.run_cmdline(["python", "bin/agnos-srcgen.py", "-o", outdir, path])
    
    def runTest(self):
        self.run_srcgen("ut/mextra", "ut/gen-mextra")



if __name__ == '__main__':
    unittest.main()


