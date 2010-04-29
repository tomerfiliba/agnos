from .volumes import Volume
from .utils import round_size, VOL_SIZE_DIVISOR


#:: @exception
class PoolSizeError(Exception):
    #:: @attr msg type=string
    pass


#:: @class
class Pool(object):
    #:: @attr name type=string access=get
    #:: @attr total_size type=int64 access=get
    #:: @attr used_size type=int64 access=get
    #:: @attr volumes type=list[Volume] access=get
    
    def __init__(self, system, name, size):
        self.system = system
        self.name = name
        self.total_size = size
        self.used_size = 0
        self.volumes = []
    
    #:: @method type=Volume
    #::    @arg name type=string
    #::    @arg size type=int64
    def create_volume(self, name, size):
        size = round_size(size)
        self.alloc(size)
        v = Volume(self, name, size)
        self.volumes.append(v)
        return v

    def alloc(self, size):
        assert size % VOL_SIZE_DIVISOR == 0
        remaining = self.total_size - self.used_size
        if size > remaining:
            raise PoolSizeError("pool is too small")
        self.used_size += size

    #:: @method
    def delete(self):
        pass















