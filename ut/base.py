import sys
import os
import unittest
from subprocess import Popen, PIPE


class TargetTest(unittest.TestCase):
    def setUp(self):
        dir = os.path.dirname(os.path.abspath(__file__))
        self.ROOT_DIR = os.path.normpath(os.path.join(dir, ".."))

    def REL(self, *args):
        return os.path.join(self.ROOT_DIR, *args)

    def spawn(self, cmdline, cwd = None, redirect = True):
        return Popen(cmdline, shell = False, stdin = PIPE if redirect else None, 
            stdout = PIPE if redirect else None, stderr = PIPE if redirect else None, cwd = cwd)

    def run_cmdline(self, cmdline, cwd = None, stdin = None, rc = 0, redirect = True):
        proc = self.spawn(cmdline, cwd, redirect = redirect)
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
        self.run_cmdline([sys.executable, "bin/agnosc", "-t", target, 
            "-o", outdir, filename], cwd = self.ROOT_DIR)








