import sys
import agnos 
from datetime import datetime
from base import TargetTest


class FeatureTestClient(TargetTest):
    def runTest(self):
        self.run_agnosc("python", "ut/features.xml", "ut/python-test")
        sys.path.append(self.REL("ut/python-test"))
        import FeatureTest_bindings
        global FeatureTest
        FeatureTest = FeatureTest_bindings
        
        conn = FeatureTest.Client.connect_executable(self.REL("ut/python-test/server.py"))
        
        try:
            self.mytest(conn)
        finally:
            conn.close()

    def mytest(self, conn):
        eve = conn.Person.init("eve", None, None)
        adam = conn.Person.init("adam", None, None)
        eve.marry(adam)
        cain = conn.Person.init("cain", adam, eve)
        
        self.assertEquals(cain.name, "cain")
        self.assertRaises(FeatureTest.MartialStatusError, adam.marry, eve)
        
        everything = conn.func_of_everything(
            1, 2, 3, 4, 5.5, True, datetime.now(), "\xff\xee\xaa\xbb", "hello world", 
            [1.3, FeatureTest.pi, 4.4], {34:"foo", 56:"bar"}, 
            FeatureTest.Address(FeatureTest.State.NY, "albany", "microsoft drive", 1772),
            eve)

        self.assertEquals(adam.think(17, 3), 17/3.0)        
        self.assertRaises(agnos.GenericException, adam.think, 17, 0)        
        

if __name__ == "__main__":
    import unittest
    unittest.main()

