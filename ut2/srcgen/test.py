import os
import unittest
from datetime import datetime
from base import TargetTest


class SrcgenTest(TargetTest):
    def run_agnos_srcgen(self, target, rootdir, outdir):
        print "agnos-srcgen %s --> %s" % (rootdir, outdir)
        self.run_cmdline(["python", "bin/agnos-srcgen.py", "-o", outdir, rootdir], cwd = self.ROOT_DIR)

    def runTest(self):
        self.run_agnos_srcgen("python", "ut2/srcgen/mextra", "ut2/srcgen")
    

if __name__ == "__main__":
    unittest.main()

