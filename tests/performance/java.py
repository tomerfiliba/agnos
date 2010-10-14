import os
import sys
import signal
import unittest
import time
from subprocess import Popen, PIPE



class JavaPerformanceTest(unittest.TestCase):
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
        self.run_cmdline([sys.executable, "bin/agnosc", "-t", target, "-o", 
            outdir, filename], cwd = self.ROOT_DIR)

    ##########################################################################
    
    def compile_java(self, path, output, classpath=[]):
        path = self.REL(path)
        self.run_cmdline(["rm", "-rf", "build"], cwd=path, rc=None)
        self.run_cmdline(["mkdir", "build"], cwd=path)
        print "javac %s" % (path,)
        cmdline = ["javac", "-g", "-cp", ":".join(classpath), "-d", "build"]
        srcs = set()
        for root, dirs, files in os.walk(path):
            srcs.update(os.path.join(dir, fn) for dir, _, fns in os.walk(path) for fn in fns if fn.endswith(".java"))
        cmdline.extend(srcs)
        self.run_cmdline(cmdline, cwd=path)
        print "jar %s" % (path,)
        self.run_cmdline(["jar", "cf", "thejar.jar", "."], cwd=os.path.join(path, "build"))
        self.run_cmdline(["mv", "build/thejar.jar", output], cwd=path)
        #self.run_cmdline("rm -rf build", cwd=path)
        return os.path.abspath(os.path.join(path, output))
    
    def run_java(self, classname, classpath):
        cmdline = ["java", "-cp", ":".join(classpath)]
        if isinstance(classname, str):
            classname = [classname]
        cmdline.extend(classname)
        return self.spawn(cmdline)
    
    def runTest(self):
        self.run_agnosc("java", "ut/performance/filesystem.xml", "ut/performance")
        agnos_jar = self.REL("lib/java/build/jars/agnos.jar")
        filesystem_jar = self.compile_java("ut/performance/filesystem", "../filesystem.jar", 
            classpath = [agnos_jar])
        test_jar = self.compile_java("ut/performance/test", "../test.jar", 
            classpath = [agnos_jar, filesystem_jar])

        serverproc = self.run_java(["myserver", "-m", "lib"], [agnos_jar, filesystem_jar, test_jar])
        time.sleep(1)
        if serverproc.poll() is not None:
            print "server stdout: ", serverproc.stdout.read()
            print "server stderr: ", serverproc.stderr.read()
            self.fail("server failed to start")
        
        try:
            banner = serverproc.stdout.readline().strip()
            self.failUnless(banner == "AGNOS", banner)
            host, port = serverproc.stdout.read().splitlines()[:2]
            clientproc = self.run_java(["myclient", host, port], [agnos_jar, filesystem_jar, test_jar])
    
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


