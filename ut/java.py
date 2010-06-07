import os
import signal
import unittest
import time
from base import TargetTest


class TestJava(TargetTest):
    def ant(self, path, target = "jar"):
        print "ant %s %s" % (target, path,)
        out, err = self.run_cmdline(["ant", "jar"], cwd=self.REL(path))
        jar = None
        for line in out.splitlines():
            if line.strip().startswith("[jar] Building jar:"):
                jar = line.strip()[20:]
        if not jar:
            print out
            self.fail("could not find created jar")
        return os.path.abspath(jar)
    
    def compile_java(self, path, output, classpath=[]):
        path = self.REL(path)
        self.run_cmdline(["rm", "-rf", "build"], cwd=path, rc=None)
        self.run_cmdline(["mkdir", "build"], cwd=path)
        print "javac %s" % (path,)
        cmdline = ["javac", "-g", "-cp", ":".join(classpath), "-d", "build"]
        cmdline.extend(fn for fn in os.listdir(path) if fn.endswith(".java"))
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
        agnos_jar = self.ant("lib/java")
        self.run_agnosc("java", "ut/features.xml", "ut/gen-java")
        features_jar = self.compile_java("ut/gen-java", "Features.jar", 
            classpath = [agnos_jar])
        test_jar = self.compile_java("ut/java-test", "test.jar", 
            classpath = [agnos_jar, features_jar])
        
        serverproc = self.run_java(["myserver", "-m", "lib"], [agnos_jar, features_jar, test_jar])
        time.sleep(1)
        if serverproc.poll() is not None:
            print "server stdout: ", serverproc.stdout.read()
            print "server stderr: ", serverproc.stderr.read()
            self.fail("server failed to start")
        
        try:
            host, port = serverproc.stdout.read().splitlines()[:2]
            clientproc = self.run_java(["myclient", host, port], [agnos_jar, features_jar, test_jar])
    
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


if __name__ == '__main__':
    unittest.main()


