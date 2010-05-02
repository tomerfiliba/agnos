from .utils import round_size


#:: @exception
class VolSizeError(Exception):
    #:: @attr msg type=string
    pass

#:: @class
class Volume(object):
    #:: @attr name type=string access=get
    #:: @attr size type=int64 access=get
    #:: @attr pool type=Pool access=get
    
    def __init__(self, pool, name, size):
        self.pool = pool
        self.name = name
        self.size = size
    
    #:: @method
    def delete(self):
        pass
    
    #:: @method
    #::    @arg newsize type=int64
    def resize(self, newsize):
        newsize = round_size(newsize)
        if newsize < self.size:
            raise VolSizeError("cannot shrink volume")
        delta = newsize - self.size
        self.pool.alloc(delta)
        self.size = newsize



