import os
import unittest
from datetime import datetime
from base import TargetTest


class SrcgenTest(TargetTest):
    def run_agnos_pysrcgen(self, target, rootdir, outdir):
        print "agnosrc-py %s --> %s" % (rootdir, outdir)
        self.run_cmdline(["python", "compiler/bin/agnosrc-py", "-o", outdir, rootdir], cwd = self.ROOT_DIR)

    def runTest(self):
        self.run_agnos_pysrcgen("python", "tests/mextra", "tests/gen-mextra")


if __name__ == "__main__":
    unittest.main()

