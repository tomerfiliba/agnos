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
    
    #:: @staticmethod type=Volume
    #::    @arg pool type=Pool
    #::    @arg name type=string
    #::    @arg size type=int64
    @classmethod
    def create_volume(cls, pool, name, size):
        v = Volume(pool, name, size)
        pool.volumes.append(v)
        return v



