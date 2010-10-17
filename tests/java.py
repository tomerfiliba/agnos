import os
import signal
import unittest
import time
from base import TargetTest


class TestJava(TargetTest):
    def generate_sconstruct(self, path):
        with open(self.REL(os.path.join(path, "SConstruct")), "w") as f:
            lines = [
                "import os",
                "import agnos_toolchain",
                "",
                "Decider('MD5')",
                "",
                "agnos_jar = SConscript(os.path.join(agnos_toolchain.__path__[0], 'libagnos/java/SConstruct'))",
                "env = Environment(",
                "    JAVACLASSPATH = [str(agnos_jar)],",
                ")",
                "env['JARCHDIR'] = os.path.join(env.Dir('.').get_abspath(), 'classes')",
                "",
                "env.Java(target = 'classes', source = 'FeatureTest')",
                "bindings_jar = env.Jar(target = 'FeatureTest.jar', source = 'classes')[0]",
                "",
                "outputs = [agnos_jar, bindings_jar]",
                "Return('outputs')",
            ]
            for l in lines:
                f.write(l + "\n")

    def runTest(self):
        self.run_agnosc("java", "tests/features.xml", "tests/java-test/bindings")
        print "scons"
        self.generate_sconstruct("tests/java-test/bindings")
        self.run_cmdline("scons", cwd = self.REL("tests/java-test"))
        
        print "./myserver -m lib"
        serverproc = self.spawn(["./myserver.sh", "-m", "lib"], cwd = self.REL("tests/java-test"))
        time.sleep(1)
        if serverproc.poll() is not None:
            print "server stdout: ", serverproc.stdout.read()
            print "server stderr: ", serverproc.stderr.read()
            self.fail("server failed to start")

        try:
            banner = serverproc.stdout.readline().strip()
            self.failUnless(banner == "AGNOS", banner)
            host = serverproc.stdout.readline().strip()
            port = serverproc.stdout.readline().strip()
            print "./myclient", host, port
            clientproc = self.spawn(["./myclient.sh", host, port], cwd = self.REL("tests/java-test"))
    
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


