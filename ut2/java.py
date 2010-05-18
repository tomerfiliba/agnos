import os
import signal
import unittest
from base import TargetTest


class TestJava(TargetTest):
    def ant_jar(self, path, target = "jar"):
        print "ant %s %s" % (target, path,)
        out, err = self.run_cmdline("ant jar", cwd=path)
        jar = None
        for line in out.splitlines():
            if line.strip().startswith("[jar] Building jar:"):
                jar = line.strip()[20:]
        if not jar:
            print out
            self.fail("could not find created jar")
        return os.path.abspath(jar)
    
    def javac(self, path, output, classpath=[]):
        self.run_cmdline("rm -rf build || true", cwd=path)
        self.run_cmdline("mkdir build", cwd=path)
        print "javac %s" % (path,)
        self.run_cmdline("javac -g -cp %s -d build *.java" % (":".join(classpath),), cwd=path)
        print "jar %s" % (path,)
        self.run_cmdline("jar cf thejar.jar .", cwd=os.path.join(path, "build"))
        self.run_cmdline("mv build/thejar.jar %s" % (output,), cwd=path)
        self.run_cmdline("rm -rf build", cwd=path)
        return os.path.abspath(os.path.join(path, output))
    
    def javarun(self, classname, classpath):
        return self.spawn("java -cp %s %s" % (":".join(classpath), classname))
    
    def run_agnosc(self, target, filename, outdir):
        print "agnosc %s" % (filename,)
        self.run_cmdline("bin/agnosc.py -t %s -o %s %s" % (target, outdir, filename))
    
    def runTest(self):
        agnos_jar = self.ant_jar("lib/java")
        self.run_agnosc("java", "ut2/RemoteFiles.xml", "ut2/gen-java")
        remotefiles_jar = self.javac("ut2/gen-java", "RemoteFiles.jar", classpath = [agnos_jar])
        test_jar = self.javac("ut2/javatest", "test.jar", classpath = [agnos_jar, remotefiles_jar])
        serverproc = self.javarun("myserver", [agnos_jar, remotefiles_jar, test_jar])
        clientproc = self.javarun("myclient", [agnos_jar, remotefiles_jar, test_jar])
        self.assertTrue(clientproc.wait() == 0)
        print "===client output==="
        print clientproc.stdout.read()
        print "==================="
        serverproc.send_signal(signal.SIGINT)
        self.assertTrue(serverproc.wait() == 0)



if __name__ == '__main__':
    unittest.main()

