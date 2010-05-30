import agnos
import unittest
import NuclearFamily_bindings as NuclearFamily


class NuclearTest(unittest.TestCase):
    def setUp(self):
        self.client = NuclearFamily.Client.connect_executable("./nuke_server.py")
    
    def tearDown(self):
        self.client.close()
    
    def runTest(self):
        eve = self.client.get_person(NuclearFamily.MOTHER_OF_ALL_ID)
        adam = eve.spouse
        print eve, adam
        print "%s lives at %s" % (eve.name, eve.address)
        
        cain = eve.give_birth(adam)
        cain.name = "cain"
        
        abel = eve.give_birth(adam)
        abel.name = "abel"
        
        self.assertRaises(NuclearFamily.MartialStatusError, cain.marry, abel)
        self.assertRaises(agnos.GenericException, adam.give_birth, eve)
            
        self.assertEquals(eve.children, [cain, abel]) 
        self.assertEquals(adam.children, [cain, abel]) 
        
        cain.address.city = "houston"
        self.assertEquals(cain.address.city, "dallas")
        
        cain.address = NuclearFamily.Address(NuclearFamily.State.TX, "houston", "shadow of death", 1)
        self.assertEquals(cain.address.city, "houston")


if __name__ == '__main__':
    unittest.main()


