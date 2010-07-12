from .pools import Pool
from .hardware import Rack, ComponentID, ComponentTypes
from .utils import round_size, VOL_SIZE_DIVISOR


#:: @class
class StorageSystem(object):
    #:: @attr name=total_size type=int64 access=get
    #:: @attr name=pools type=list[Pool] access=get
    #:: @attr name=racks type=list[Rack] access=get

    def __init__(self, size):
        self.total_size = round_size(size)
        self.pools = []
        self.racks = []
    
    #:: @attr type=int64 access=get
    @property
    def used_size(self):
        return sum(p.used_size for p in self.pools)
    
    def create_rack(self):
        self.racks.append(Rack(self, ComponentID(len(self.racks) + 1, ComponentTypes.RACK)))
    
    #:: @method type=Pool
    #::     @arg name type=string
    #::     @arg size type=int64
    def create_pool(self, name, size):
        p = Pool(self, name, size)
        self.pools.append(p)
        return p


TheSystem = None

#:: @func type=StorageSystem
def get_system():
    global TheSystem
    if not TheSystem:
        TheSystem = StorageSystem(1000 * VOL_SIZE_DIVISOR)
        TheSystem.create_rack()
        TheSystem.create_rack()
        p1 = TheSystem.create_pool("moshe", 200 * VOL_SIZE_DIVISOR)
        p2 = TheSystem.create_pool("baruch", 100 * VOL_SIZE_DIVISOR)
        p1.create_volume("vol1", 20 * VOL_SIZE_DIVISOR)
        p1.create_volume("vol2", 15 * VOL_SIZE_DIVISOR)
        p1.create_volume("vol3", 24 * VOL_SIZE_DIVISOR)
    
    return TheSystem


