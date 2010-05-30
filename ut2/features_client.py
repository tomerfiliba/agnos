import unittest
from datetime import datetime
import FeatureTest_bindings as FeatureTest


class FeatureTestClient(unittest.TestCase):
    def setUp(self):
        self.conn = FeatureTest.Client.connect_executable("./features_server.py")
    
    def tearDown(self):
        self.conn.close()
    
    def runTest(self):
        eve = self.conn.Person.init("eve", None, None)
        adam = self.conn.Person.init("adam", None, None)
        eve.marry(adam)
        cain = self.conn.Person.init("cain", adam, eve)
        print cain
        
        self.assertEquals(cain.name, "cain")
        self.assertRaises(FeatureTest.MartialStatusError, adam.marry, eve)
        
        everything = self.conn.func_of_everything(
            1, 2, 3, 4, 5.5, True, datetime.now(), "\xff\xfe", "hello world", 
            [1.3, FeatureTest.pi, 4.4], {34:"foo", 56:"bar"}, 
            FeatureTest.Address(FeatureTest.State.NY, "albany", "microsoft drive", 1772),
            eve)
        
        print everything
        


if __name__ == '__main__':
    unittest.main()


