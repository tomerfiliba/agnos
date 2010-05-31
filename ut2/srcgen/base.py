import sys
import os
import unittest
from subprocess import Popen, PIPE


class TargetTest(unittest.TestCase):
    def setUp(self):
        dir = os.path.dirname(os.path.abspath(__file__))
        self.ROOT_DIR = os.path.normpath(os.path.join(dir, "..", ".."))

    def REL(self, *args):
        return os.path.join(self.ROOT_DIR, *args)

    def spawn(self, cmdline, cwd = None):
        return Popen(cmdline, shell = False, stdin = PIPE, 
            stdout = PIPE, stderr = PIPE, cwd = cwd)

    def run_cmdline(self, cmdline, cwd = None, stdin = None, rc = 0):
        proc = self.spawn(cmdline, cwd)
        stdout, stderr = proc.communicate(stdin)
        if rc is not None and proc.returncode != rc:
            print "Process execution error: %r" % (cmdline,)
            if stdout.strip():
                print "===stdout==="
                print stdout
            if stderr.strip():
                print "===stderr==="
                print stderr
            self.fail("external process failed")
        return stdout, stderr

    def run_agnosc(self, target, filename, outdir):
        print "agnosc %s --> %s" % (filename, outdir)
        self.run_cmdline(["python", "bin/agnosc.py", "-t", target, "-o", outdir, filename], cwd = self.ROOT_DIR)
    







