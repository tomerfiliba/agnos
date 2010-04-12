import sys
sys.path.append("../gen-py")

import agnos 
from agnos.servers import SimpleServer
import RemoteFiles


c = RemoteFiles.Client.connect("localhost", 17731)
f = c.open("/tmp/foo", "w")
print f
f.write("hello world")
s = f.stat()
print s
try:
    f.read(10)
except RemoteFiles.UnderlyingIOError, ex:
    print ex
f.close()
try:
    f.write("dlrow olleh")
except agnos.GenericError, ex:
    print ex

f1 = c.open("/tmp/foo", "r")
f2 = c.open("/tmp/foo2", "w")
c.copy(f1, f2)
f1.close()
f2.close()

f2 = c.open("/tmp/foo2", "r")
data = f2.read(100)
print "copy = %r" % (data,)
