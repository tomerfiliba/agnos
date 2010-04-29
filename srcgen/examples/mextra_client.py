from subprocess import Popen, PIPE
import mextra_bindings
from agnos.protocol import GenericError


c = mextra_bindings.Client.connect_child("./mextra_server.py")
s = c.get_system()
print "---"
print s.total_size

