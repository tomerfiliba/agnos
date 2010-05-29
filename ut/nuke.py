#!/usr/bin/env python
import itertools
import random
from datetime import datetime
import NuclearFamily_bindings as NuclearFamily


cars = []
houses = []
people = {}


class Asset(object):
    def __init__(self, owner, value):
        self.owner = owner
        self.value = value
    def sell(self, new_owner):
        self.owner = new_owner

class House(Asset):
    def __init__(self, value, address):
        Asset.__init__(self, None, value)
        self.address = address
        houses.append(self)
    
    def rent(self, tenant):
        pass

class Car(Asset):
    def __init__(self, value, make, model):
        Asset.__init__(self, None, value)
        self.make = make
        self.model = model
        self.milage = 0
        cars.append(self)
    
    def drive(self, distance):
        if distance < 0:
            raise ValueError("distance must be positive")
        self.milage += distance

_person_id_counter = itertools.count(NuclearFamily.MOTHER_OF_ALL_ID)

class Person(Asset):
    def __init__(self, name, father, mother, sex):
        self.id = _person_id_counter.next()
        self.name = name
        self.father = father
        self.mother = mother
        self.children = []
        self.spouse = None
        self.address = NuclearFamily.Address(NuclearFamily.State.TX, "dallas", "cranberry rd", 6772)
        self.date_of_birth = datetime.now()
        self.sex = sex
        people[self.id] = self
    
    def divorce(self):
        if not self.spouse:
            raise NuclearFamily.MartialStatusError("does not have a spouse", self)
        self.spouse.spouse = None
        self.spouse = None
    def marry(self, partner):
        if self.spouse:
            raise NuclearFamily.MartialStatusError("already married", self)
        if partner.spouse:
            raise NuclearFamily.MartialStatusError("already married", partner)
        self.spouse = partner
        partner = self
    def give_birth(self, father):
        if self.sex != NuclearFamily.Sex.FEMALE:
            raise ValueError("only females can give birth")
        if father is None and self.spouse:
            father = self.spouse
        if father.sex != NuclearFamily.Sex.MALE:
            raise ValueError("father must be a male")
        sex = random.choice([NuclearFamily.Sex.MALE, NuclearFamily.Sex.FEMALE])
        child = Person("unnamed", father, self, sex)
        self.children.append(child)
        father.children.append(child)
        return child

class Handler(NuclearFamily.IHandler):
    def get_cars(self):
        return cars
    def get_houses(self):
        return houses
    def get_person(self, id):
        return people[id]


eve = Person("eve", None, None, NuclearFamily.Sex.FEMALE)
adam = Person("adam", None, None, NuclearFamily.Sex.MALE)
eve.marry(adam)

c1 = Car(17000, NuclearFamily.Manufacturer.GMC, "savana")
c2 = Car(18000, NuclearFamily.Manufacturer.Toyota, "corolla")
h1 = House(160000, NuclearFamily.Address(NuclearFamily.State.IL, "chicago", "floopy st", 2345))
h2 = House(190000, NuclearFamily.Address(NuclearFamily.State.IL, "chicago", "floopy st", 2346))

if __name__ == "__main__":
    from agnos.servers import server_main
    server_main(NuclearFamily.Processor(Handler()))










