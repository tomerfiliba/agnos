import os


class TargetBase(object):
    def __init__(self, path):
        self.path = path
    
    def generate(self, service):
        raise NotImplementedError()
    
    def mkdir(self, name):
        os.makedirs(os.path.join(self.path, name))
    
    def open(self, filename, mode = "w"):
        return open(os.path.join(self.path, filename), mode)



