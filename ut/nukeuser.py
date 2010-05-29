import agnos
import NuclearFamily_bindings as NuclearFamily


c = NuclearFamily.Client.connect_executable("./nuke.py")
p = c.get_person(NuclearFamily.MOTHER_OF_ALL_ID)
print p
print p.address

