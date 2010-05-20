#:: @module mextra.hardware


#:: @enum
class ComponentTypes(object):
    #:: @member RACK value=1
    RACK = 1
    #:: @member MODULE value=2
    MODULE = 2
    #:: @member DISK value=3
    DISK = 3

#:: @record
class ComponentID(object):
    #:: @attr rack type=int32
    #:: @attr comptype type=ComponentTypes
    #:: @attr module type=int32
    #:: @attr slot type=int32
    
    def __init__(self, rack, comptype, module = 0, slot = 0):
        self.rack = rack
        self.comptype = comptype
        self.module = module
        self.slot = slot
    
    def __repr__(self):
        if self.slot:
            return "%d:%d:%d:%d" % (self.rack, self.comptype, self.module, self.slot)
        elif self.module:
            return "%d:%d:%d" % (self.rack, self.comptype, self.module)
        else:
            return "%d:%d" % (self.rack, self.comptype)

#:: @enum ComponentStatus
class ComponentStatus(object):
    #:: @member OK value=0
    OK = 0
    #:: @member MISSING value=1
    MISSING = 1
    #:: @member HWERROR value=2
    HWERROR = 2
    #:: @member PHASING_IN value=3
    PHASING_IN = 3
    #:: @member PHASING_OUT value=4
    PHASING_OUT = 4
    #:: @member PHASED_OUT value=5
    PHASED_OUT = 5
    #:: @member PHASED_IN value=6
    PHASED_IN = 6

#:: @class
class Disk(object):
    #:: @attr compid type=ComponentID access=get 
    def __init__(self, module, compid):
        self.module = module
        self.compid = compid
    
    #:: @method type=ComponentStatus
    def get_status(self):
        return ComponentStatus.OK

#:: @class
class HWModule(object):
    #:: @attr compid type=ComponentID access=get 
    #:: @attr disks type=list[Disk] access=get
     
    def __init__(self, rack, compid):
        self.rack = rack
        self.compid = compid
        self.disks = [
            Disk(self, ComponentID(compid.rack, ComponentTypes.DISK, compid.module, i))
            for i in range(1, 13)
            ]
    
    #:: @method type=ComponentStatus
    def get_status(self):
        return ComponentStatus.OK

#:: @class
class Rack(object):
    #:: @attr compid type=ComponentID access=get 
    #:: @attr modules type=list[HWModule] access=get
    
    def __init__(self, system, compid):
        self.system = system
        self.compid = compid
        self.modules = [
            HWModule(self, ComponentID(compid.rack, ComponentTypes.MODULE, i))
            for i in range(1, 16)
            ]
    
    #:: @method type=ComponentStatus
    def get_status(self):
        return ComponentStatus.OK














