import mextra_bindings
#from agnos.protocol import GenericException


c = mextra_bindings.Client.connect_subproc("./mextra_server.py")
s = c.get_system()
print s.total_size
print s.pools
p = s.pools[0]
v = p.volumes[2]
print v
print v.size
v.resize(v.size * 2)
print v.size
print s.used_size
v2 = c.Volume.create_volume(p, "krok", 888222)
print v2
print p.volumes
v3 = p.volumes[3]
print v2 == v3

