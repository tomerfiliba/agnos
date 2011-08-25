#!/usr/bin/env python
from agnos import HeteroMap
from datetime import datetime
import FeatureTest_bindings as FeatureTest


class ClassA(object):
    def __init__(self, attr1, attr2):
        self.attr1 = attr1
        self.attr2 = attr2
    def method1(self, a, b):
        return int(a) + (7 if b else 3)

class ClassB(ClassA):
    def __init__(self, attr1, attr2, attr3):
        ClassA.__init__(self, attr1, attr2)
        self.attr3 = attr3
    def method2(self, a, b):
        return int(a) + (90 if b else 30)

class ClassC(ClassB):
    def __init__(self, attr1, attr2, attr3, attr4):
        ClassB.__init__(self, attr1, attr2, attr3)
        self.attr4 = attr4
    def method3(self, a, b):
        return int(a) + (22 if b else -22)

class Person(object):
    def __init__(self, name, father, mother):
        self.name = name
        self.date_of_birth = datetime.now()
        self.father = father
        self.mother = mother
        self.spouse = None
        self.address = FeatureTest.Address(FeatureTest.State.TX, "dallas", "cranberry rd", 6772)
    
    def divorce(self):
        if not self.spouse:
            raise FeatureTest.MartialStatusError("does not have a spouse", self)
        self.spouse.spouse = None
        self.spouse = None
    
    def think(self, a, b):
        return a / b
    
    def marry(self, partner):
        if self.spouse:
            raise FeatureTest.MartialStatusError("already married", self)
        if partner.spouse:
            raise FeatureTest.MartialStatusError("already married", partner)
        if (self.mother and self.mother == partner.mother) or (self.father and self.father == partner.father):
            raise FeatureTest.MartialStatusError("siblings cannot marry", partner)
        self.spouse = partner
        partner.spouse = self


class Handler(FeatureTest.IHandler):
    def get_record_b(self, ):
        return FeatureTest.RecordB(17, 18, 19)

    def Person_init(self, name, father, mother):
        return Person(name, father, mother)
    
    def get_class_c(self, ):
        return [ClassC(4, 5, 6.0, [ClassA(1,2), ClassA(2,4)]),
            ClassC(33, 12, 76.2, [ClassA(5,7), ClassA(3,3)]),
            ClassC(77, 88, 99.11, [ClassA(2,7), ClassA(1,1)])] 
    
    def func_of_everything(self, a, b, c, d, e, f, g, h, i, j, k, l, m, n, o):
        return FeatureTest.Everything(a, b, c, d, e, f, g, h, i, j, k, l, m, n)
    
    def hmap_test(self, a, b):
        hm = HeteroMap()
        hm["a"] = a
        hm["b"] = 18
        return hm


if __name__ == "__main__":
    from agnos.servers import server_main
    server_main(FeatureTest.ProcessorFactory(Handler()))










