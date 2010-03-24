import os


class TargetBase(object):
    def __init__(self, path):
        self.path = path
        self.mkdir("")
    
    def generate(self, service):
        raise NotImplementedError()
    
    def mkdir(self, name):
        fullname = os.path.join(self.path, name)
        if not os.path.isdir(fullname):
            os.makedirs(fullname)
    
    def open(self, filename, mode = "w"):
        return open(os.path.join(self.path, filename), mode)



