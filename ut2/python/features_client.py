import os
import unittest
from datetime import datetime
from base import TargetTest


class FeatureTestClient(TargetTest):
    def runTest(self):
        self.run_agnosc("python", "ut2/features.xml", "ut2/python")
        import FeatureTest_bindings
        global FeatureTest
        FeatureTest = FeatureTest_bindings
        
        conn = FeatureTest.Client.connect_executable(self.REL("ut2/python/features_server.py"))
        
        try:
            self.mytest(conn)
        finally:
            conn.close()

    def mytest(self, conn):
        eve = conn.Person.init("eve", None, None)
        adam = conn.Person.init("adam", None, None)
        eve.marry(adam)
        cain = conn.Person.init("cain", adam, eve)
        print cain
        
        self.assertEquals(cain.name, "cain")
        self.assertRaises(FeatureTest.MartialStatusError, adam.marry, eve)
        
        everything = conn.func_of_everything(
            1, 2, 3, 4, 5.5, True, datetime.now(), "\xff\xee\xaa\xbb", "hello world", 
            [1.3, FeatureTest.pi, 4.4], {34:"foo", 56:"bar"}, 
            FeatureTest.Address(FeatureTest.State.NY, "albany", "microsoft drive", 1772),
            eve)
        
        print everything
        

if __name__ == "__main__":
    unittest.main()

