import os
import unittest
from subprocess import Popen, PIPE


class TargetTest(unittest.TestCase):
    ROOT_DIR = "../"
    
    def setUp(self):
        os.chdir(self.ROOT_DIR)

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
        print "agnosc %s" % (filename,)
        self.run_cmdline(["bin/agnosc.py", "-t", target, "-o", outdir, filename])
    
    def open(self, filename, mode="r"):
        if not isinstance(filename, str):
            filename = os.path.join(*filename)
        return open(filename, mode)








