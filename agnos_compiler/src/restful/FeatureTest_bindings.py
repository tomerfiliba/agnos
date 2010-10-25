import agnos
from agnos import packers
from agnos import utils
from functools import partial

AGNOS_TOOLCHAIN_VERSION = '1.0.0'
AGNOS_PROTOCOL_VERSION = 'AGNOS-1.0'
IDL_MAGIC = 'd9c0cdeaa37fd00f508e6913e1ee6a3355d07b52'
CLIENT_VERSION = None
SUPPORTED_VERSIONS = []

#
# enums
#
State = utils.create_enum('State', {
    'TX' : 0, 
    'NY' : 1, 
    'IL' : 2, 
    'CA' : 3})

class StatePacker(packers.Packer):
    @classmethod
    def get_id(cls):
        return 900006
    @classmethod
    def pack(cls, obj, stream):
        if isinstance(obj, utils.Enum):
            packers.Int32.pack(obj.value, stream)
        else:
            packers.Int32.pack(obj, stream)
    @classmethod
    def unpack(cls, stream):
        return State.get_by_value(packers.Int32.unpack(stream))

#
# records
#
class RecordA(object):
    _recid = 900101
    _ATTRS = ['ob_refcount', 'ob_type']
    
    def __init__(self, ob_refcount = None, ob_type = None):
        self.ob_refcount = ob_refcount
        self.ob_type = ob_type
    
    def __repr__(self):
        attrs = [self.ob_refcount, self.ob_type]
        return 'RecordA(%s)' % (', '.join(repr(a) for a in attrs),)

class Address(object):
    _recid = 900011
    _ATTRS = ['state', 'city', 'street', 'num']
    
    def __init__(self, state = None, city = None, street = None, num = None):
        self.state = state
        self.city = city
        self.street = street
        self.num = num
    
    def __repr__(self):
        attrs = [self.state, self.city, self.street, self.num]
        return 'Address(%s)' % (', '.join(repr(a) for a in attrs),)

class Everything(object):
    _recid = 900058
    _ATTRS = ['some_int8', 'some_int16', 'some_int32', 'some_int64', 'some_float', 'some_bool', 'some_date', 'some_buffer', 'some_string', 'some_list', 'some_set', 'some_map', 'some_record', 'some_class']
    
    def __init__(self, some_int8 = None, some_int16 = None, some_int32 = None, some_int64 = None, some_float = None, some_bool = None, some_date = None, some_buffer = None, some_string = None, some_list = None, some_set = None, some_map = None, some_record = None, some_class = None):
        self.some_int8 = some_int8
        self.some_int16 = some_int16
        self.some_int32 = some_int32
        self.some_int64 = some_int64
        self.some_float = some_float
        self.some_bool = some_bool
        self.some_date = some_date
        self.some_buffer = some_buffer
        self.some_string = some_string
        self.some_list = some_list
        self.some_set = some_set
        self.some_map = some_map
        self.some_record = some_record
        self.some_class = some_class
    
    def __repr__(self):
        attrs = [self.some_int8, self.some_int16, self.some_int32, self.some_int64, self.some_float, self.some_bool, self.some_date, self.some_buffer, self.some_string, self.some_list, self.some_set, self.some_map, self.some_record, self.some_class]
        return 'Everything(%s)' % (', '.join(repr(a) for a in attrs),)

class RecordB(object):
    _recid = 900103
    _ATTRS = ['ob_refcount', 'ob_type', 'intval']
    
    def __init__(self, ob_refcount = None, ob_type = None, intval = None):
        self.ob_refcount = ob_refcount
        self.ob_type = ob_type
        self.intval = intval
    
    def __repr__(self):
        attrs = [self.ob_refcount, self.ob_type, self.intval]
        return 'RecordB(%s)' % (', '.join(repr(a) for a in attrs),)

class MartialStatusError(agnos.PackedException):
    _recid = 900014
    _ATTRS = ['message', 'person']
    
    def __init__(self, message = None, person = None):
        self.message = message
        self.person = person
    
    def __repr__(self):
        attrs = [self.message, self.person]
        return 'MartialStatusError(%s)' % (', '.join(repr(a) for a in attrs),)

class RecordAPacker(packers.Packer):
    @classmethod
    def get_id(cls):
        return 900101
    @classmethod
    def pack(cls, obj, stream):
        packers.Int32.pack(obj.ob_refcount, stream)
        packers.Int32.pack(obj.ob_type, stream)
    @classmethod
    def unpack(cls, stream):
        return RecordA(
            packers.Int32.unpack(stream),
            packers.Int32.unpack(stream),
        )

class AddressPacker(packers.Packer):
    @classmethod
    def get_id(cls):
        return 900011
    @classmethod
    def pack(cls, obj, stream):
        StatePacker.pack(obj.state, stream)
        packers.Str.pack(obj.city, stream)
        packers.Str.pack(obj.street, stream)
        packers.Int32.pack(obj.num, stream)
    @classmethod
    def unpack(cls, stream):
        return Address(
            StatePacker.unpack(stream),
            packers.Str.unpack(stream),
            packers.Str.unpack(stream),
            packers.Int32.unpack(stream),
        )

class RecordBPacker(packers.Packer):
    @classmethod
    def get_id(cls):
        return 900103
    @classmethod
    def pack(cls, obj, stream):
        packers.Int32.pack(obj.ob_refcount, stream)
        packers.Int32.pack(obj.ob_type, stream)
        packers.Int64.pack(obj.intval, stream)
    @classmethod
    def unpack(cls, stream):
        return RecordB(
            packers.Int32.unpack(stream),
            packers.Int32.unpack(stream),
            packers.Int64.unpack(stream),
        )

#
# consts
#
BITMASK = 1024
pi = 3.1415926535000001

#
# classes
#
class PersonProxy(agnos.BaseProxy):
    __slots__ = []
    
    def _get_name(self):
        return self._client._funcs.sync_900134(self)
    name = property(_get_name)
    def _get_date_of_birth(self):
        return self._client._funcs.sync_900136(self)
    date_of_birth = property(_get_date_of_birth)
    def _get_address(self):
        return self._client._funcs.sync_900138(self)
    def _set_address(self, value):
        self._client._funcs.sync_900138(self, value)
    address = property(_get_address, _set_address)
    def _get_father(self):
        return self._client._funcs.sync_900140(self)
    father = property(_get_father)
    def _get_mother(self):
        return self._client._funcs.sync_900142(self)
    mother = property(_get_mother)
    def _get_spouse(self):
        return self._client._funcs.sync_900144(self)
    spouse = property(_get_spouse)
    
    def marry(self, partner):
        return self._client._funcs.sync_900146(self, partner)
    def divorce(self, ):
        return self._client._funcs.sync_900147(self)
    def think(self, a, b):
        return self._client._funcs.sync_900148(self, a, b)

class ClassAProxy(agnos.BaseProxy):
    __slots__ = []
    
    def _get_attr1(self):
        return self._client._funcs.sync_900109(self)
    def _set_attr1(self, value):
        self._client._funcs.sync_900109(self, value)
    attr1 = property(_get_attr1, _set_attr1)
    def _get_attr2(self):
        return self._client._funcs.sync_900111(self)
    def _set_attr2(self, value):
        self._client._funcs.sync_900111(self, value)
    attr2 = property(_get_attr2, _set_attr2)
    
    def method1(self, a, b):
        return self._client._funcs.sync_900113(self, a, b)
    
    # downcasts
    def cast_to_ClassB():
        return ClassBProxy(self._client, self._objref, False)
    def cast_to_ClassC():
        return ClassCProxy(self._client, self._objref, False)

class ClassBProxy(agnos.BaseProxy):
    __slots__ = []
    
    def _get_attr1(self):
        return self._client._funcs.sync_900114(self)
    def _set_attr1(self, value):
        self._client._funcs.sync_900114(self, value)
    attr1 = property(_get_attr1, _set_attr1)
    def _get_attr2(self):
        return self._client._funcs.sync_900116(self)
    def _set_attr2(self, value):
        self._client._funcs.sync_900116(self, value)
    attr2 = property(_get_attr2, _set_attr2)
    def _get_attr3(self):
        return self._client._funcs.sync_900119(self)
    def _set_attr3(self, value):
        self._client._funcs.sync_900119(self, value)
    attr3 = property(_get_attr3, _set_attr3)
    
    def method1(self, a, b):
        return self._client._funcs.sync_900118(self, a, b)
    def method2(self, a, b):
        return self._client._funcs.sync_900121(self, a, b)
    
    # downcasts
    def cast_to_ClassC():
        return ClassCProxy(self._client, self._objref, False)
    
    # upcasts
    def cast_to_ClassA():
        return ClassAProxy(self._client, self._objref, False)

class ClassCProxy(agnos.BaseProxy):
    __slots__ = []
    
    def _get_attr1(self):
        return self._client._funcs.sync_900122(self)
    def _set_attr1(self, value):
        self._client._funcs.sync_900122(self, value)
    attr1 = property(_get_attr1, _set_attr1)
    def _get_attr2(self):
        return self._client._funcs.sync_900124(self)
    def _set_attr2(self, value):
        self._client._funcs.sync_900124(self, value)
    attr2 = property(_get_attr2, _set_attr2)
    def _get_attr3(self):
        return self._client._funcs.sync_900126(self)
    def _set_attr3(self, value):
        self._client._funcs.sync_900126(self, value)
    attr3 = property(_get_attr3, _set_attr3)
    def _get_attr4(self):
        return self._client._funcs.sync_900131(self)
    attr4 = property(_get_attr4)
    
    def method1(self, a, b):
        return self._client._funcs.sync_900128(self, a, b)
    def method2(self, a, b):
        return self._client._funcs.sync_900129(self, a, b)
    def method3(self, a, b):
        return self._client._funcs.sync_900133(self, a, b)
    
    # upcasts
    def cast_to_ClassB():
        return ClassBProxy(self._client, self._objref, False)
    def cast_to_ClassA():
        return ClassAProxy(self._client, self._objref, False)


#
# server
#
class IHandler(object):
    __slots__ = []
    def get_class_c(self, ):
        raise NotImplementedError()
    def func_of_everything(self, a, b, c, d, e, f, g, h, i, j, k, l, m, n):
        raise NotImplementedError()
    def get_record_b(self, ):
        raise NotImplementedError()
    def Person_init(self, name, father, mother):
        raise NotImplementedError()

class Processor(agnos.BaseProcessor):
    def __init__(self, transport, handler, exception_map = {}):
        agnos.BaseProcessor.__init__(self, transport)
        def _func_900125(args):
            obj = args.pop(0)
            obj.attr2 = args[0]
        def _unpack_900125():
            return [
                ClassCObjRef.unpack(self.transport),
                packers.Int32.unpack(self.transport),
            ]
        def _func_900127(args):
            obj = args.pop(0)
            obj.attr3 = args[0]
        def _unpack_900127():
            return [
                ClassCObjRef.unpack(self.transport),
                packers.Float.unpack(self.transport),
            ]
        def _func_900123(args):
            obj = args.pop(0)
            obj.attr1 = args[0]
        def _unpack_900123():
            return [
                ClassCObjRef.unpack(self.transport),
                packers.Int32.unpack(self.transport),
            ]
        def _func_900148(args):
            obj = args.pop(0)
            return obj.think(*args)
        def _unpack_900148():
            return [
                PersonObjRef.unpack(self.transport),
                packers.Float.unpack(self.transport),
                packers.Float.unpack(self.transport),
            ]
        def _func_900120(args):
            obj = args.pop(0)
            obj.attr3 = args[0]
        def _unpack_900120():
            return [
                ClassBObjRef.unpack(self.transport),
                packers.Float.unpack(self.transport),
            ]
        def _func_900117(args):
            obj = args.pop(0)
            obj.attr2 = args[0]
        def _unpack_900117():
            return [
                ClassBObjRef.unpack(self.transport),
                packers.Int32.unpack(self.transport),
            ]
        def _func_900115(args):
            obj = args.pop(0)
            obj.attr1 = args[0]
        def _unpack_900115():
            return [
                ClassBObjRef.unpack(self.transport),
                packers.Int32.unpack(self.transport),
            ]
        def _func_900138(args):
            obj = args.pop(0)
            return obj.address
        def _unpack_900138():
            return [
                PersonObjRef.unpack(self.transport),
            ]
        def _func_900136(args):
            obj = args.pop(0)
            return obj.date_of_birth
        def _unpack_900136():
            return [
                PersonObjRef.unpack(self.transport),
            ]
        def _func_900140(args):
            obj = args.pop(0)
            return obj.father
        def _unpack_900140():
            return [
                PersonObjRef.unpack(self.transport),
            ]
        def _func_900113(args):
            obj = args.pop(0)
            return obj.method1(*args)
        def _unpack_900113():
            return [
                ClassAObjRef.unpack(self.transport),
                packers.Str.unpack(self.transport),
                packers.Bool.unpack(self.transport),
            ]
        def _func_900109(args):
            obj = args.pop(0)
            return obj.attr1
        def _unpack_900109():
            return [
                ClassAObjRef.unpack(self.transport),
            ]
        def _func_900111(args):
            obj = args.pop(0)
            return obj.attr2
        def _unpack_900111():
            return [
                ClassAObjRef.unpack(self.transport),
            ]
        def _func_900121(args):
            obj = args.pop(0)
            return obj.method2(*args)
        def _unpack_900121():
            return [
                ClassBObjRef.unpack(self.transport),
                packers.Str.unpack(self.transport),
                packers.Bool.unpack(self.transport),
            ]
        def _func_900118(args):
            obj = args.pop(0)
            return obj.method1(*args)
        def _unpack_900118():
            return [
                ClassBObjRef.unpack(self.transport),
                packers.Str.unpack(self.transport),
                packers.Bool.unpack(self.transport),
            ]
        def _func_900147(args):
            obj = args.pop(0)
            return obj.divorce(*args)
        def _unpack_900147():
            return [
                PersonObjRef.unpack(self.transport),
            ]
        def _func_900110(args):
            obj = args.pop(0)
            obj.attr1 = args[0]
        def _unpack_900110():
            return [
                ClassAObjRef.unpack(self.transport),
                packers.Int32.unpack(self.transport),
            ]
        def _func_900112(args):
            obj = args.pop(0)
            obj.attr2 = args[0]
        def _unpack_900112():
            return [
                ClassAObjRef.unpack(self.transport),
                packers.Int32.unpack(self.transport),
            ]
        def _func_900098(args):
            return handler.get_class_c(*args)
        def _unpack_900098():
            return []
        def _func_900073(args):
            return handler.func_of_everything(*args)
        def _unpack_900073():
            return [
                packers.Int8.unpack(self.transport),
                packers.Int16.unpack(self.transport),
                packers.Int32.unpack(self.transport),
                packers.Int64.unpack(self.transport),
                packers.Float.unpack(self.transport),
                packers.Bool.unpack(self.transport),
                packers.Date.unpack(self.transport),
                packers.Buffer.unpack(self.transport),
                packers.Str.unpack(self.transport),
                _list_float.unpack(self.transport),
                _set_int32.unpack(self.transport),
                _map_int32_str.unpack(self.transport),
                AddressPacker.unpack(self.transport),
                PersonObjRef.unpack(self.transport),
            ]
        def _func_900142(args):
            obj = args.pop(0)
            return obj.mother
        def _unpack_900142():
            return [
                PersonObjRef.unpack(self.transport),
            ]
        def _func_900134(args):
            obj = args.pop(0)
            return obj.name
        def _unpack_900134():
            return [
                PersonObjRef.unpack(self.transport),
            ]
        def _func_900131(args):
            obj = args.pop(0)
            return obj.attr4
        def _unpack_900131():
            return [
                ClassCObjRef.unpack(self.transport),
            ]
        def _func_900124(args):
            obj = args.pop(0)
            return obj.attr2
        def _unpack_900124():
            return [
                ClassCObjRef.unpack(self.transport),
            ]
        def _func_900126(args):
            obj = args.pop(0)
            return obj.attr3
        def _unpack_900126():
            return [
                ClassCObjRef.unpack(self.transport),
            ]
        def _func_900122(args):
            obj = args.pop(0)
            return obj.attr1
        def _unpack_900122():
            return [
                ClassCObjRef.unpack(self.transport),
            ]
        def _func_900119(args):
            obj = args.pop(0)
            return obj.attr3
        def _unpack_900119():
            return [
                ClassBObjRef.unpack(self.transport),
            ]
        def _func_900116(args):
            obj = args.pop(0)
            return obj.attr2
        def _unpack_900116():
            return [
                ClassBObjRef.unpack(self.transport),
            ]
        def _func_900114(args):
            obj = args.pop(0)
            return obj.attr1
        def _unpack_900114():
            return [
                ClassBObjRef.unpack(self.transport),
            ]
        def _func_900144(args):
            obj = args.pop(0)
            return obj.spouse
        def _unpack_900144():
            return [
                PersonObjRef.unpack(self.transport),
            ]
        def _func_900139(args):
            obj = args.pop(0)
            obj.address = args[0]
        def _unpack_900139():
            return [
                PersonObjRef.unpack(self.transport),
                AddressPacker.unpack(self.transport),
            ]
        def _func_900104(args):
            return handler.get_record_b(*args)
        def _unpack_900104():
            return []
        def _func_900146(args):
            obj = args.pop(0)
            return obj.marry(*args)
        def _unpack_900146():
            return [
                PersonObjRef.unpack(self.transport),
                PersonObjRef.unpack(self.transport),
            ]
        def _func_900133(args):
            obj = args.pop(0)
            return obj.method3(*args)
        def _unpack_900133():
            return [
                ClassCObjRef.unpack(self.transport),
                packers.Str.unpack(self.transport),
                packers.Bool.unpack(self.transport),
            ]
        def _func_900129(args):
            obj = args.pop(0)
            return obj.method2(*args)
        def _unpack_900129():
            return [
                ClassCObjRef.unpack(self.transport),
                packers.Str.unpack(self.transport),
                packers.Bool.unpack(self.transport),
            ]
        def _func_900128(args):
            obj = args.pop(0)
            return obj.method1(*args)
        def _unpack_900128():
            return [
                ClassCObjRef.unpack(self.transport),
                packers.Str.unpack(self.transport),
                packers.Bool.unpack(self.transport),
            ]
        def _func_900043(args):
            return handler.Person_init(*args)
        def _unpack_900043():
            return [
                packers.Str.unpack(self.transport),
                PersonObjRef.unpack(self.transport),
                PersonObjRef.unpack(self.transport),
            ]
        
        self.exception_map = exception_map
        storer = self.store
        loader = self.load
        PersonObjRef = packers.ObjRef(900039, storer, loader)
        ClassAObjRef = packers.ObjRef(900083, storer, loader)
        ClassBObjRef = packers.ObjRef(900090, storer, loader)
        ClassCObjRef = packers.ObjRef(900097, storer, loader)
        
        packers_map = {}
        heteroMapPacker = packers.HeteroMapPacker(999, packers_map)
        packers_map[999] = heteroMapPacker
        
        class EverythingPacker(packers.Packer):
            @classmethod
            def get_id(cls):
                return 900058
            @classmethod
            def pack(cls, obj, stream):
                packers.Int8.pack(obj.some_int8, stream)
                packers.Int16.pack(obj.some_int16, stream)
                packers.Int32.pack(obj.some_int32, stream)
                packers.Int64.pack(obj.some_int64, stream)
                packers.Float.pack(obj.some_float, stream)
                packers.Bool.pack(obj.some_bool, stream)
                packers.Date.pack(obj.some_date, stream)
                packers.Buffer.pack(obj.some_buffer, stream)
                packers.Str.pack(obj.some_string, stream)
                _list_float.pack(obj.some_list, stream)
                _set_int32.pack(obj.some_set, stream)
                _map_int32_str.pack(obj.some_map, stream)
                AddressPacker.pack(obj.some_record, stream)
                PersonObjRef.pack(obj.some_class, stream)
            @classmethod
            def unpack(cls, stream):
                return Everything(
                    packers.Int8.unpack(stream),
                    packers.Int16.unpack(stream),
                    packers.Int32.unpack(stream),
                    packers.Int64.unpack(stream),
                    packers.Float.unpack(stream),
                    packers.Bool.unpack(stream),
                    packers.Date.unpack(stream),
                    packers.Buffer.unpack(stream),
                    packers.Str.unpack(stream),
                    _list_float.unpack(stream),
                    _set_int32.unpack(stream),
                    _map_int32_str.unpack(stream),
                    AddressPacker.unpack(stream),
                    PersonObjRef.unpack(stream),
                )
        
        class MartialStatusErrorPacker(packers.Packer):
            @classmethod
            def get_id(cls):
                return 900014
            @classmethod
            def pack(cls, obj, stream):
                packers.Str.pack(obj.message, stream)
                PersonObjRef.pack(obj.person, stream)
            @classmethod
            def unpack(cls, stream):
                return MartialStatusError(
                    packers.Str.unpack(stream),
                    PersonObjRef.unpack(stream),
                )
        
        _list_float = packers.ListOf(900106, packers.Float)
        _set_int32 = packers.SetOf(900107, packers.Int32)
        _map_int32_str = packers.MapOf(900108, packers.Int32, packers.Str)
        _list_ClassA = packers.ListOf(900130, ClassAObjRef)
        _list_ClassC = packers.ListOf(900149, ClassCObjRef)
        
        self.func_mapping = {
            900125 : (_func_900125, _unpack_900125, None),
            900127 : (_func_900127, _unpack_900127, None),
            900123 : (_func_900123, _unpack_900123, None),
            900148 : (_func_900148, _unpack_900148, packers.Float),
            900120 : (_func_900120, _unpack_900120, None),
            900117 : (_func_900117, _unpack_900117, None),
            900115 : (_func_900115, _unpack_900115, None),
            900138 : (_func_900138, _unpack_900138, AddressPacker),
            900136 : (_func_900136, _unpack_900136, packers.Date),
            900140 : (_func_900140, _unpack_900140, PersonObjRef),
            900113 : (_func_900113, _unpack_900113, packers.Int32),
            900109 : (_func_900109, _unpack_900109, packers.Int32),
            900111 : (_func_900111, _unpack_900111, packers.Int32),
            900121 : (_func_900121, _unpack_900121, packers.Int32),
            900118 : (_func_900118, _unpack_900118, packers.Int32),
            900147 : (_func_900147, _unpack_900147, None),
            900110 : (_func_900110, _unpack_900110, None),
            900112 : (_func_900112, _unpack_900112, None),
            900098 : (_func_900098, _unpack_900098, _list_ClassC),
            900073 : (_func_900073, _unpack_900073, EverythingPacker),
            900142 : (_func_900142, _unpack_900142, PersonObjRef),
            900134 : (_func_900134, _unpack_900134, packers.Str),
            900131 : (_func_900131, _unpack_900131, _list_ClassA),
            900124 : (_func_900124, _unpack_900124, packers.Int32),
            900126 : (_func_900126, _unpack_900126, packers.Float),
            900122 : (_func_900122, _unpack_900122, packers.Int32),
            900119 : (_func_900119, _unpack_900119, packers.Float),
            900116 : (_func_900116, _unpack_900116, packers.Int32),
            900114 : (_func_900114, _unpack_900114, packers.Int32),
            900144 : (_func_900144, _unpack_900144, PersonObjRef),
            900139 : (_func_900139, _unpack_900139, None),
            900104 : (_func_900104, _unpack_900104, RecordBPacker),
            900146 : (_func_900146, _unpack_900146, None),
            900133 : (_func_900133, _unpack_900133, packers.Int32),
            900129 : (_func_900129, _unpack_900129, packers.Int32),
            900128 : (_func_900128, _unpack_900128, packers.Int32),
            900043 : (_func_900043, _unpack_900043, PersonObjRef),
        }
        
        self.packed_exceptions = {
            MartialStatusError : MartialStatusErrorPacker,
        }
        
        packers_map[900103] = RecordBPacker
        packers_map[900101] = RecordAPacker
        packers_map[900058] = EverythingPacker
        packers_map[900090] = ClassBObjRef
        packers_map[900014] = MartialStatusErrorPacker
        packers_map[900097] = ClassCObjRef
        packers_map[900083] = ClassAObjRef
        packers_map[900039] = PersonObjRef
        packers_map[900006] = StatePacker
        packers_map[900011] = AddressPacker
    
    def process_get_general_info(self, info):
        info["AGNOS_TOOLCHAIN_VERSION"] = AGNOS_TOOLCHAIN_VERSION
        info["AGNOS_PROTOCOL_VERSION"] = AGNOS_PROTOCOL_VERSION
        info["IDL_MAGIC"] = IDL_MAGIC
        info["SERVICE_NAME"] = "FeatureTest"
        info.add("SUPPORTED_VERSIONS", packers.Str, SUPPORTED_VERSIONS, packers.list_of_str)
    
    def process_get_functions_info(self, info):
        funcinfo = info.new_map(900125)
        funcinfo["name"] = "_ClassC_set_attr2"
        funcinfo["type"] = "void"
        arg_names = []
        arg_types = []
        arg_names.append("_proxy")
        arg_types.append("ClassC")
        arg_names.append("value")
        arg_types.append("int32")
        funcinfo.add("arg_names", packers.Str, arg_names, packers.list_of_str)
        funcinfo.add("arg_types", packers.Str, arg_types, packers.list_of_str)
        funcinfo = info.new_map(900127)
        funcinfo["name"] = "_ClassC_set_attr3"
        funcinfo["type"] = "void"
        arg_names = []
        arg_types = []
        arg_names.append("_proxy")
        arg_types.append("ClassC")
        arg_names.append("value")
        arg_types.append("float")
        funcinfo.add("arg_names", packers.Str, arg_names, packers.list_of_str)
        funcinfo.add("arg_types", packers.Str, arg_types, packers.list_of_str)
        funcinfo = info.new_map(900123)
        funcinfo["name"] = "_ClassC_set_attr1"
        funcinfo["type"] = "void"
        arg_names = []
        arg_types = []
        arg_names.append("_proxy")
        arg_types.append("ClassC")
        arg_names.append("value")
        arg_types.append("int32")
        funcinfo.add("arg_names", packers.Str, arg_names, packers.list_of_str)
        funcinfo.add("arg_types", packers.Str, arg_types, packers.list_of_str)
        funcinfo = info.new_map(900148)
        funcinfo["name"] = "_Person_think"
        funcinfo["type"] = "float"
        arg_names = []
        arg_types = []
        arg_names.append("_proxy")
        arg_types.append("Person")
        arg_names.append("a")
        arg_types.append("float")
        arg_names.append("b")
        arg_types.append("float")
        funcinfo.add("arg_names", packers.Str, arg_names, packers.list_of_str)
        funcinfo.add("arg_types", packers.Str, arg_types, packers.list_of_str)
        funcinfo = info.new_map(900120)
        funcinfo["name"] = "_ClassB_set_attr3"
        funcinfo["type"] = "void"
        arg_names = []
        arg_types = []
        arg_names.append("_proxy")
        arg_types.append("ClassB")
        arg_names.append("value")
        arg_types.append("float")
        funcinfo.add("arg_names", packers.Str, arg_names, packers.list_of_str)
        funcinfo.add("arg_types", packers.Str, arg_types, packers.list_of_str)
        funcinfo = info.new_map(900117)
        funcinfo["name"] = "_ClassB_set_attr2"
        funcinfo["type"] = "void"
        arg_names = []
        arg_types = []
        arg_names.append("_proxy")
        arg_types.append("ClassB")
        arg_names.append("value")
        arg_types.append("int32")
        funcinfo.add("arg_names", packers.Str, arg_names, packers.list_of_str)
        funcinfo.add("arg_types", packers.Str, arg_types, packers.list_of_str)
        funcinfo = info.new_map(900115)
        funcinfo["name"] = "_ClassB_set_attr1"
        funcinfo["type"] = "void"
        arg_names = []
        arg_types = []
        arg_names.append("_proxy")
        arg_types.append("ClassB")
        arg_names.append("value")
        arg_types.append("int32")
        funcinfo.add("arg_names", packers.Str, arg_names, packers.list_of_str)
        funcinfo.add("arg_types", packers.Str, arg_types, packers.list_of_str)
        funcinfo = info.new_map(900138)
        funcinfo["name"] = "_Person_get_address"
        funcinfo["type"] = "Address"
        arg_names = []
        arg_types = []
        arg_names.append("_proxy")
        arg_types.append("Person")
        funcinfo.add("arg_names", packers.Str, arg_names, packers.list_of_str)
        funcinfo.add("arg_types", packers.Str, arg_types, packers.list_of_str)
        funcinfo = info.new_map(900136)
        funcinfo["name"] = "_Person_get_date_of_birth"
        funcinfo["type"] = "date"
        arg_names = []
        arg_types = []
        arg_names.append("_proxy")
        arg_types.append("Person")
        funcinfo.add("arg_names", packers.Str, arg_names, packers.list_of_str)
        funcinfo.add("arg_types", packers.Str, arg_types, packers.list_of_str)
        funcinfo = info.new_map(900140)
        funcinfo["name"] = "_Person_get_father"
        funcinfo["type"] = "Person"
        arg_names = []
        arg_types = []
        arg_names.append("_proxy")
        arg_types.append("Person")
        funcinfo.add("arg_names", packers.Str, arg_names, packers.list_of_str)
        funcinfo.add("arg_types", packers.Str, arg_types, packers.list_of_str)
        funcinfo = info.new_map(900113)
        funcinfo["name"] = "_ClassA_method1"
        funcinfo["type"] = "int32"
        arg_names = []
        arg_types = []
        arg_names.append("_proxy")
        arg_types.append("ClassA")
        arg_names.append("a")
        arg_types.append("str")
        arg_names.append("b")
        arg_types.append("bool")
        funcinfo.add("arg_names", packers.Str, arg_names, packers.list_of_str)
        funcinfo.add("arg_types", packers.Str, arg_types, packers.list_of_str)
        funcinfo = info.new_map(900109)
        funcinfo["name"] = "_ClassA_get_attr1"
        funcinfo["type"] = "int32"
        arg_names = []
        arg_types = []
        arg_names.append("_proxy")
        arg_types.append("ClassA")
        funcinfo.add("arg_names", packers.Str, arg_names, packers.list_of_str)
        funcinfo.add("arg_types", packers.Str, arg_types, packers.list_of_str)
        funcinfo = info.new_map(900111)
        funcinfo["name"] = "_ClassA_get_attr2"
        funcinfo["type"] = "int32"
        arg_names = []
        arg_types = []
        arg_names.append("_proxy")
        arg_types.append("ClassA")
        funcinfo.add("arg_names", packers.Str, arg_names, packers.list_of_str)
        funcinfo.add("arg_types", packers.Str, arg_types, packers.list_of_str)
        funcinfo = info.new_map(900121)
        funcinfo["name"] = "_ClassB_method2"
        funcinfo["type"] = "int32"
        arg_names = []
        arg_types = []
        arg_names.append("_proxy")
        arg_types.append("ClassB")
        arg_names.append("a")
        arg_types.append("str")
        arg_names.append("b")
        arg_types.append("bool")
        funcinfo.add("arg_names", packers.Str, arg_names, packers.list_of_str)
        funcinfo.add("arg_types", packers.Str, arg_types, packers.list_of_str)
        funcinfo = info.new_map(900118)
        funcinfo["name"] = "_ClassB_method1"
        funcinfo["type"] = "int32"
        arg_names = []
        arg_types = []
        arg_names.append("_proxy")
        arg_types.append("ClassB")
        arg_names.append("a")
        arg_types.append("str")
        arg_names.append("b")
        arg_types.append("bool")
        funcinfo.add("arg_names", packers.Str, arg_names, packers.list_of_str)
        funcinfo.add("arg_types", packers.Str, arg_types, packers.list_of_str)
        funcinfo = info.new_map(900147)
        funcinfo["name"] = "_Person_divorce"
        funcinfo["type"] = "void"
        arg_names = []
        arg_types = []
        arg_names.append("_proxy")
        arg_types.append("Person")
        funcinfo.add("arg_names", packers.Str, arg_names, packers.list_of_str)
        funcinfo.add("arg_types", packers.Str, arg_types, packers.list_of_str)
        funcinfo = info.new_map(900110)
        funcinfo["name"] = "_ClassA_set_attr1"
        funcinfo["type"] = "void"
        arg_names = []
        arg_types = []
        arg_names.append("_proxy")
        arg_types.append("ClassA")
        arg_names.append("value")
        arg_types.append("int32")
        funcinfo.add("arg_names", packers.Str, arg_names, packers.list_of_str)
        funcinfo.add("arg_types", packers.Str, arg_types, packers.list_of_str)
        funcinfo = info.new_map(900112)
        funcinfo["name"] = "_ClassA_set_attr2"
        funcinfo["type"] = "void"
        arg_names = []
        arg_types = []
        arg_names.append("_proxy")
        arg_types.append("ClassA")
        arg_names.append("value")
        arg_types.append("int32")
        funcinfo.add("arg_names", packers.Str, arg_names, packers.list_of_str)
        funcinfo.add("arg_types", packers.Str, arg_types, packers.list_of_str)
        funcinfo = info.new_map(900098)
        funcinfo["name"] = "get_class_c"
        funcinfo["type"] = "list[ClassC]"
        arg_names = []
        arg_types = []
        funcinfo.add("arg_names", packers.Str, arg_names, packers.list_of_str)
        funcinfo.add("arg_types", packers.Str, arg_types, packers.list_of_str)
        funcinfo = info.new_map(900073)
        funcinfo["name"] = "func_of_everything"
        funcinfo["type"] = "Everything"
        arg_names = []
        arg_types = []
        arg_names.append("a")
        arg_types.append("int8")
        arg_names.append("b")
        arg_types.append("int16")
        arg_names.append("c")
        arg_types.append("int32")
        arg_names.append("d")
        arg_types.append("int64")
        arg_names.append("e")
        arg_types.append("float")
        arg_names.append("f")
        arg_types.append("bool")
        arg_names.append("g")
        arg_types.append("date")
        arg_names.append("h")
        arg_types.append("buffer")
        arg_names.append("i")
        arg_types.append("str")
        arg_names.append("j")
        arg_types.append("list[float]")
        arg_names.append("k")
        arg_types.append("set[int32]")
        arg_names.append("l")
        arg_types.append("map[int32, str]")
        arg_names.append("m")
        arg_types.append("Address")
        arg_names.append("n")
        arg_types.append("Person")
        funcinfo.add("arg_names", packers.Str, arg_names, packers.list_of_str)
        funcinfo.add("arg_types", packers.Str, arg_types, packers.list_of_str)
        funcinfo = info.new_map(900142)
        funcinfo["name"] = "_Person_get_mother"
        funcinfo["type"] = "Person"
        arg_names = []
        arg_types = []
        arg_names.append("_proxy")
        arg_types.append("Person")
        funcinfo.add("arg_names", packers.Str, arg_names, packers.list_of_str)
        funcinfo.add("arg_types", packers.Str, arg_types, packers.list_of_str)
        funcinfo = info.new_map(900134)
        funcinfo["name"] = "_Person_get_name"
        funcinfo["type"] = "str"
        arg_names = []
        arg_types = []
        arg_names.append("_proxy")
        arg_types.append("Person")
        funcinfo.add("arg_names", packers.Str, arg_names, packers.list_of_str)
        funcinfo.add("arg_types", packers.Str, arg_types, packers.list_of_str)
        funcinfo = info.new_map(900131)
        funcinfo["name"] = "_ClassC_get_attr4"
        funcinfo["type"] = "list[ClassA]"
        arg_names = []
        arg_types = []
        arg_names.append("_proxy")
        arg_types.append("ClassC")
        funcinfo.add("arg_names", packers.Str, arg_names, packers.list_of_str)
        funcinfo.add("arg_types", packers.Str, arg_types, packers.list_of_str)
        funcinfo = info.new_map(900124)
        funcinfo["name"] = "_ClassC_get_attr2"
        funcinfo["type"] = "int32"
        arg_names = []
        arg_types = []
        arg_names.append("_proxy")
        arg_types.append("ClassC")
        funcinfo.add("arg_names", packers.Str, arg_names, packers.list_of_str)
        funcinfo.add("arg_types", packers.Str, arg_types, packers.list_of_str)
        funcinfo = info.new_map(900126)
        funcinfo["name"] = "_ClassC_get_attr3"
        funcinfo["type"] = "float"
        arg_names = []
        arg_types = []
        arg_names.append("_proxy")
        arg_types.append("ClassC")
        funcinfo.add("arg_names", packers.Str, arg_names, packers.list_of_str)
        funcinfo.add("arg_types", packers.Str, arg_types, packers.list_of_str)
        funcinfo = info.new_map(900122)
        funcinfo["name"] = "_ClassC_get_attr1"
        funcinfo["type"] = "int32"
        arg_names = []
        arg_types = []
        arg_names.append("_proxy")
        arg_types.append("ClassC")
        funcinfo.add("arg_names", packers.Str, arg_names, packers.list_of_str)
        funcinfo.add("arg_types", packers.Str, arg_types, packers.list_of_str)
        funcinfo = info.new_map(900119)
        funcinfo["name"] = "_ClassB_get_attr3"
        funcinfo["type"] = "float"
        arg_names = []
        arg_types = []
        arg_names.append("_proxy")
        arg_types.append("ClassB")
        funcinfo.add("arg_names", packers.Str, arg_names, packers.list_of_str)
        funcinfo.add("arg_types", packers.Str, arg_types, packers.list_of_str)
        funcinfo = info.new_map(900116)
        funcinfo["name"] = "_ClassB_get_attr2"
        funcinfo["type"] = "int32"
        arg_names = []
        arg_types = []
        arg_names.append("_proxy")
        arg_types.append("ClassB")
        funcinfo.add("arg_names", packers.Str, arg_names, packers.list_of_str)
        funcinfo.add("arg_types", packers.Str, arg_types, packers.list_of_str)
        funcinfo = info.new_map(900114)
        funcinfo["name"] = "_ClassB_get_attr1"
        funcinfo["type"] = "int32"
        arg_names = []
        arg_types = []
        arg_names.append("_proxy")
        arg_types.append("ClassB")
        funcinfo.add("arg_names", packers.Str, arg_names, packers.list_of_str)
        funcinfo.add("arg_types", packers.Str, arg_types, packers.list_of_str)
        funcinfo = info.new_map(900144)
        funcinfo["name"] = "_Person_get_spouse"
        funcinfo["type"] = "Person"
        arg_names = []
        arg_types = []
        arg_names.append("_proxy")
        arg_types.append("Person")
        funcinfo.add("arg_names", packers.Str, arg_names, packers.list_of_str)
        funcinfo.add("arg_types", packers.Str, arg_types, packers.list_of_str)
        funcinfo = info.new_map(900139)
        funcinfo["name"] = "_Person_set_address"
        funcinfo["type"] = "void"
        arg_names = []
        arg_types = []
        arg_names.append("_proxy")
        arg_types.append("Person")
        arg_names.append("value")
        arg_types.append("Address")
        funcinfo.add("arg_names", packers.Str, arg_names, packers.list_of_str)
        funcinfo.add("arg_types", packers.Str, arg_types, packers.list_of_str)
        funcinfo = info.new_map(900104)
        funcinfo["name"] = "get_record_b"
        funcinfo["type"] = "RecordB"
        arg_names = []
        arg_types = []
        funcinfo.add("arg_names", packers.Str, arg_names, packers.list_of_str)
        funcinfo.add("arg_types", packers.Str, arg_types, packers.list_of_str)
        funcinfo = info.new_map(900146)
        funcinfo["name"] = "_Person_marry"
        funcinfo["type"] = "void"
        arg_names = []
        arg_types = []
        arg_names.append("_proxy")
        arg_types.append("Person")
        arg_names.append("partner")
        arg_types.append("Person")
        funcinfo.add("arg_names", packers.Str, arg_names, packers.list_of_str)
        funcinfo.add("arg_types", packers.Str, arg_types, packers.list_of_str)
        funcinfo = info.new_map(900133)
        funcinfo["name"] = "_ClassC_method3"
        funcinfo["type"] = "int32"
        arg_names = []
        arg_types = []
        arg_names.append("_proxy")
        arg_types.append("ClassC")
        arg_names.append("a")
        arg_types.append("str")
        arg_names.append("b")
        arg_types.append("bool")
        funcinfo.add("arg_names", packers.Str, arg_names, packers.list_of_str)
        funcinfo.add("arg_types", packers.Str, arg_types, packers.list_of_str)
        funcinfo = info.new_map(900129)
        funcinfo["name"] = "_ClassC_method2"
        funcinfo["type"] = "int32"
        arg_names = []
        arg_types = []
        arg_names.append("_proxy")
        arg_types.append("ClassC")
        arg_names.append("a")
        arg_types.append("str")
        arg_names.append("b")
        arg_types.append("bool")
        funcinfo.add("arg_names", packers.Str, arg_names, packers.list_of_str)
        funcinfo.add("arg_types", packers.Str, arg_types, packers.list_of_str)
        funcinfo = info.new_map(900128)
        funcinfo["name"] = "_ClassC_method1"
        funcinfo["type"] = "int32"
        arg_names = []
        arg_types = []
        arg_names.append("_proxy")
        arg_types.append("ClassC")
        arg_names.append("a")
        arg_types.append("str")
        arg_names.append("b")
        arg_types.append("bool")
        funcinfo.add("arg_names", packers.Str, arg_names, packers.list_of_str)
        funcinfo.add("arg_types", packers.Str, arg_types, packers.list_of_str)
        funcinfo = info.new_map(900043)
        funcinfo["name"] = "init"
        funcinfo["type"] = "Person"
        arg_names = []
        arg_types = []
        arg_names.append("name")
        arg_types.append("str")
        arg_names.append("father")
        arg_types.append("Person")
        arg_names.append("mother")
        arg_types.append("Person")
        funcinfo.add("arg_names", packers.Str, arg_names, packers.list_of_str)
        funcinfo.add("arg_types", packers.Str, arg_types, packers.list_of_str)
    
    def process_get_function_codes(self, info):
        info["_ClassC_set_attr2"] = 900125
        info["_ClassC_set_attr3"] = 900127
        info["_ClassC_set_attr1"] = 900123
        info["_Person_think"] = 900148
        info["_ClassB_set_attr3"] = 900120
        info["_ClassB_set_attr2"] = 900117
        info["_ClassB_set_attr1"] = 900115
        info["_Person_get_address"] = 900138
        info["_Person_get_date_of_birth"] = 900136
        info["_Person_get_father"] = 900140
        info["_ClassA_method1"] = 900113
        info["_ClassA_get_attr1"] = 900109
        info["_ClassA_get_attr2"] = 900111
        info["_ClassB_method2"] = 900121
        info["_ClassB_method1"] = 900118
        info["_Person_divorce"] = 900147
        info["_ClassA_set_attr1"] = 900110
        info["_ClassA_set_attr2"] = 900112
        info["get_class_c"] = 900098
        info["func_of_everything"] = 900073
        info["_Person_get_mother"] = 900142
        info["_Person_get_name"] = 900134
        info["_ClassC_get_attr4"] = 900131
        info["_ClassC_get_attr2"] = 900124
        info["_ClassC_get_attr3"] = 900126
        info["_ClassC_get_attr1"] = 900122
        info["_ClassB_get_attr3"] = 900119
        info["_ClassB_get_attr2"] = 900116
        info["_ClassB_get_attr1"] = 900114
        info["_Person_get_spouse"] = 900144
        info["_Person_set_address"] = 900139
        info["get_record_b"] = 900104
        info["_Person_marry"] = 900146
        info["_ClassC_method3"] = 900133
        info["_ClassC_method2"] = 900129
        info["_ClassC_method1"] = 900128
        info["init"] = 900043
    
    def process_get_types_info(self, info):
        group = info.new_map("enums")
        members = group.new_map("State")
        members["TX"] = "0"
        members["NY"] = "1"
        members["IL"] = "2"
        members["CA"] = "3"
        
        group = info.new_map("records")
        members = group.new_map("RecordA")
        members["ob_refcount"] = "int32"
        members["ob_type"] = "int32"
        members = group.new_map("Address")
        members["state"] = "Enum(name='State')"
        members["city"] = "str"
        members["street"] = "str"
        members["num"] = "int32"
        members = group.new_map("Everything")
        members["some_int8"] = "int8"
        members["some_int16"] = "int16"
        members["some_int32"] = "int32"
        members["some_int64"] = "int64"
        members["some_float"] = "float"
        members["some_bool"] = "bool"
        members["some_date"] = "date"
        members["some_buffer"] = "buffer"
        members["some_string"] = "str"
        members["some_list"] = "list[float]"
        members["some_set"] = "set[int32]"
        members["some_map"] = "map[int32, str]"
        members["some_record"] = "Address"
        members["some_class"] = "Person"
        members = group.new_map("RecordB")
        members["ob_refcount"] = "int32"
        members["ob_type"] = "int32"
        members["intval"] = "int64"
        members = group.new_map("MartialStatusError")
        members["message"] = "str"
        members["person"] = "Person"
        
        group = info.new_map("classes")
        cls_group = group.new_map("Person")
        attr_group = cls_group.new_map("attrs")
        meth_group = cls_group.new_map("methods")
        a = attr_group.new_map("name")
        a["type"] = "str"
        a["get"] = True
        a["set"] = False
        a = attr_group.new_map("date_of_birth")
        a["type"] = "date"
        a["get"] = True
        a["set"] = False
        a = attr_group.new_map("address")
        a["type"] = "Address"
        a["get"] = True
        a["set"] = True
        a = attr_group.new_map("father")
        a["type"] = "Person"
        a["get"] = True
        a["set"] = False
        a = attr_group.new_map("mother")
        a["type"] = "Person"
        a["get"] = True
        a["set"] = False
        a = attr_group.new_map("spouse")
        a["type"] = "Person"
        a["get"] = True
        a["set"] = False
        m = meth_group.new_map("marry")
        m["type"] = "Person"
        arg_names = []
        arg_types = []
        arg_names.append("partner")
        arg_types.append("Person")
        m.add("arg_names", packers.Str, arg_names, packers.list_of_str)
        m.add("arg_types", packers.Str, arg_types, packers.list_of_str)
        m = meth_group.new_map("divorce")
        m["type"] = "Person"
        arg_names = []
        arg_types = []
        m.add("arg_names", packers.Str, arg_names, packers.list_of_str)
        m.add("arg_types", packers.Str, arg_types, packers.list_of_str)
        m = meth_group.new_map("think")
        m["type"] = "Person"
        arg_names = []
        arg_types = []
        arg_names.append("a")
        arg_types.append("float")
        arg_names.append("b")
        arg_types.append("float")
        m.add("arg_names", packers.Str, arg_names, packers.list_of_str)
        m.add("arg_types", packers.Str, arg_types, packers.list_of_str)
        cls_group = group.new_map("ClassA")
        attr_group = cls_group.new_map("attrs")
        meth_group = cls_group.new_map("methods")
        a = attr_group.new_map("attr1")
        a["type"] = "int32"
        a["get"] = True
        a["set"] = True
        a = attr_group.new_map("attr2")
        a["type"] = "int32"
        a["get"] = True
        a["set"] = True
        m = meth_group.new_map("method1")
        m["type"] = "float"
        arg_names = []
        arg_types = []
        arg_names.append("a")
        arg_types.append("str")
        arg_names.append("b")
        arg_types.append("bool")
        m.add("arg_names", packers.Str, arg_names, packers.list_of_str)
        m.add("arg_types", packers.Str, arg_types, packers.list_of_str)
        cls_group = group.new_map("ClassB")
        attr_group = cls_group.new_map("attrs")
        meth_group = cls_group.new_map("methods")
        a = attr_group.new_map("attr3")
        a["type"] = "float"
        a["get"] = True
        a["set"] = True
        m = meth_group.new_map("method2")
        m["type"] = "bool"
        arg_names = []
        arg_types = []
        arg_names.append("a")
        arg_types.append("str")
        arg_names.append("b")
        arg_types.append("bool")
        m.add("arg_names", packers.Str, arg_names, packers.list_of_str)
        m.add("arg_types", packers.Str, arg_types, packers.list_of_str)
        cls_group = group.new_map("ClassC")
        attr_group = cls_group.new_map("attrs")
        meth_group = cls_group.new_map("methods")
        a = attr_group.new_map("attr4")
        a["type"] = "list[ClassA]"
        a["get"] = True
        a["set"] = False
        m = meth_group.new_map("method3")
        m["type"] = "bool"
        arg_names = []
        arg_types = []
        arg_names.append("a")
        arg_types.append("str")
        arg_names.append("b")
        arg_types.append("bool")
        m.add("arg_names", packers.Str, arg_names, packers.list_of_str)
        m.add("arg_types", packers.Str, arg_types, packers.list_of_str)
    
    def process_get_service_info(self, info):
        funcs = info.new_map("functions")
        func = funcs.new_map("get_class_c")
        func["type"] = "list[ClassC]"
        arg_names = []
        arg_types = []
        func.add("arg_names", packers.Str, arg_names, packers.list_of_str)
        func.add("arg_types", packers.Str, arg_types, packers.list_of_str)
        func = funcs.new_map("func_of_everything")
        func["type"] = "Everything"
        arg_names = []
        arg_types = []
        arg_names.append("a")
        arg_types.append("int8")
        arg_names.append("b")
        arg_types.append("int16")
        arg_names.append("c")
        arg_types.append("int32")
        arg_names.append("d")
        arg_types.append("int64")
        arg_names.append("e")
        arg_types.append("float")
        arg_names.append("f")
        arg_types.append("bool")
        arg_names.append("g")
        arg_types.append("date")
        arg_names.append("h")
        arg_types.append("buffer")
        arg_names.append("i")
        arg_types.append("str")
        arg_names.append("j")
        arg_types.append("list[float]")
        arg_names.append("k")
        arg_types.append("set[int32]")
        arg_names.append("l")
        arg_types.append("map[int32, str]")
        arg_names.append("m")
        arg_types.append("Address")
        arg_names.append("n")
        arg_types.append("Person")
        func.add("arg_names", packers.Str, arg_names, packers.list_of_str)
        func.add("arg_types", packers.Str, arg_types, packers.list_of_str)
        func = funcs.new_map("get_record_b")
        func["type"] = "RecordB"
        arg_names = []
        arg_types = []
        func.add("arg_names", packers.Str, arg_names, packers.list_of_str)
        func.add("arg_types", packers.Str, arg_types, packers.list_of_str)
        func = funcs.new_map("Person.init")
        func["type"] = "Person"
        arg_names = []
        arg_types = []
        arg_names.append("name")
        arg_types.append("str")
        arg_names.append("father")
        arg_types.append("Person")
        arg_names.append("mother")
        arg_types.append("Person")
        func.add("arg_names", packers.Str, arg_names, packers.list_of_str)
        func.add("arg_types", packers.Str, arg_types, packers.list_of_str)
        consts = info.new_map("consts")
        const = consts.new_map("BITMASK")
        const["type"] = "int32"
        const["value"] = "1024"
        const = consts.new_map("pi")
        const["type"] = "float"
        const["value"] = "3.1415926535"
    

def ProcessorFactory(handler, exception_map = {}):
    return lambda transport: Processor(transport, handler, exception_map)

#
# client
#
class Client(agnos.BaseClient):
    def __init__(self, transport):
        class EverythingPacker(packers.Packer):
            @classmethod
            def get_id(cls):
                return 900058
            @classmethod
            def pack(cls, obj, stream):
                packers.Int8.pack(obj.some_int8, stream)
                packers.Int16.pack(obj.some_int16, stream)
                packers.Int32.pack(obj.some_int32, stream)
                packers.Int64.pack(obj.some_int64, stream)
                packers.Float.pack(obj.some_float, stream)
                packers.Bool.pack(obj.some_bool, stream)
                packers.Date.pack(obj.some_date, stream)
                packers.Buffer.pack(obj.some_buffer, stream)
                packers.Str.pack(obj.some_string, stream)
                _list_float.pack(obj.some_list, stream)
                _set_int32.pack(obj.some_set, stream)
                _map_int32_str.pack(obj.some_map, stream)
                AddressPacker.pack(obj.some_record, stream)
                PersonObjRef.pack(obj.some_class, stream)
            @classmethod
            def unpack(cls, stream):
                return Everything(
                    packers.Int8.unpack(stream),
                    packers.Int16.unpack(stream),
                    packers.Int32.unpack(stream),
                    packers.Int64.unpack(stream),
                    packers.Float.unpack(stream),
                    packers.Bool.unpack(stream),
                    packers.Date.unpack(stream),
                    packers.Buffer.unpack(stream),
                    packers.Str.unpack(stream),
                    _list_float.unpack(stream),
                    _set_int32.unpack(stream),
                    _map_int32_str.unpack(stream),
                    AddressPacker.unpack(stream),
                    PersonObjRef.unpack(stream),
                )
        
        class MartialStatusErrorPacker(packers.Packer):
            @classmethod
            def get_id(cls):
                return 900014
            @classmethod
            def pack(cls, obj, stream):
                packers.Str.pack(obj.message, stream)
                PersonObjRef.pack(obj.person, stream)
            @classmethod
            def unpack(cls, stream):
                return MartialStatusError(
                    packers.Str.unpack(stream),
                    PersonObjRef.unpack(stream),
                )
        
        packed_exceptions = {}
        self._utils = agnos.ClientUtils(transport, packed_exceptions)
        
        storer = lambda proxy: -1 if proxy is None else proxy._objref
        PersonObjRef = packers.ObjRef(900039, storer, partial(self._utils.get_proxy, PersonProxy, self))
        ClassAObjRef = packers.ObjRef(900083, storer, partial(self._utils.get_proxy, ClassAProxy, self))
        ClassBObjRef = packers.ObjRef(900090, storer, partial(self._utils.get_proxy, ClassBProxy, self))
        ClassCObjRef = packers.ObjRef(900097, storer, partial(self._utils.get_proxy, ClassCProxy, self))
        
        packers_map = {}
        heteroMapPacker = packers.HeteroMapPacker(999, packers_map)
        packers_map[999] = heteroMapPacker
        
        _list_float = packers.ListOf(900106, packers.Float)
        _set_int32 = packers.SetOf(900107, packers.Int32)
        _map_int32_str = packers.MapOf(900108, packers.Int32, packers.Str)
        _list_ClassA = packers.ListOf(900130, ClassAObjRef)
        _list_ClassC = packers.ListOf(900149, ClassCObjRef)
        
        packed_exceptions[900014] = MartialStatusErrorPacker
        
        packers_map[900103] = RecordBPacker
        packers_map[900101] = RecordAPacker
        packers_map[900058] = EverythingPacker
        packers_map[900090] = ClassBObjRef
        packers_map[900014] = MartialStatusErrorPacker
        packers_map[900097] = ClassCObjRef
        packers_map[900083] = ClassAObjRef
        packers_map[900039] = PersonObjRef
        packers_map[900006] = StatePacker
        packers_map[900011] = AddressPacker
        
        class Functions(object):
            def __init__(self, utils):
                self.utils = utils
            def sync_900125(_self, _proxy, value):
                with _self.utils.invocation(900125, None) as seq:
                    ClassCObjRef.pack(_proxy, _self.utils.transport)
                    packers.Int32.pack(value, _self.utils.transport)
                return _self.utils.get_reply(seq)
            def sync_900127(_self, _proxy, value):
                with _self.utils.invocation(900127, None) as seq:
                    ClassCObjRef.pack(_proxy, _self.utils.transport)
                    packers.Float.pack(value, _self.utils.transport)
                return _self.utils.get_reply(seq)
            def sync_900123(_self, _proxy, value):
                with _self.utils.invocation(900123, None) as seq:
                    ClassCObjRef.pack(_proxy, _self.utils.transport)
                    packers.Int32.pack(value, _self.utils.transport)
                return _self.utils.get_reply(seq)
            def sync_900148(_self, _proxy, a, b):
                with _self.utils.invocation(900148, packers.Float) as seq:
                    PersonObjRef.pack(_proxy, _self.utils.transport)
                    packers.Float.pack(a, _self.utils.transport)
                    packers.Float.pack(b, _self.utils.transport)
                return _self.utils.get_reply(seq)
            def sync_900120(_self, _proxy, value):
                with _self.utils.invocation(900120, None) as seq:
                    ClassBObjRef.pack(_proxy, _self.utils.transport)
                    packers.Float.pack(value, _self.utils.transport)
                return _self.utils.get_reply(seq)
            def sync_900117(_self, _proxy, value):
                with _self.utils.invocation(900117, None) as seq:
                    ClassBObjRef.pack(_proxy, _self.utils.transport)
                    packers.Int32.pack(value, _self.utils.transport)
                return _self.utils.get_reply(seq)
            def sync_900115(_self, _proxy, value):
                with _self.utils.invocation(900115, None) as seq:
                    ClassBObjRef.pack(_proxy, _self.utils.transport)
                    packers.Int32.pack(value, _self.utils.transport)
                return _self.utils.get_reply(seq)
            def sync_900138(_self, _proxy):
                with _self.utils.invocation(900138, AddressPacker) as seq:
                    PersonObjRef.pack(_proxy, _self.utils.transport)
                return _self.utils.get_reply(seq)
            def sync_900136(_self, _proxy):
                with _self.utils.invocation(900136, packers.Date) as seq:
                    PersonObjRef.pack(_proxy, _self.utils.transport)
                return _self.utils.get_reply(seq)
            def sync_900140(_self, _proxy):
                with _self.utils.invocation(900140, PersonObjRef) as seq:
                    PersonObjRef.pack(_proxy, _self.utils.transport)
                return _self.utils.get_reply(seq)
            def sync_900113(_self, _proxy, a, b):
                with _self.utils.invocation(900113, packers.Int32) as seq:
                    ClassAObjRef.pack(_proxy, _self.utils.transport)
                    packers.Str.pack(a, _self.utils.transport)
                    packers.Bool.pack(b, _self.utils.transport)
                return _self.utils.get_reply(seq)
            def sync_900109(_self, _proxy):
                with _self.utils.invocation(900109, packers.Int32) as seq:
                    ClassAObjRef.pack(_proxy, _self.utils.transport)
                return _self.utils.get_reply(seq)
            def sync_900111(_self, _proxy):
                with _self.utils.invocation(900111, packers.Int32) as seq:
                    ClassAObjRef.pack(_proxy, _self.utils.transport)
                return _self.utils.get_reply(seq)
            def sync_900121(_self, _proxy, a, b):
                with _self.utils.invocation(900121, packers.Int32) as seq:
                    ClassBObjRef.pack(_proxy, _self.utils.transport)
                    packers.Str.pack(a, _self.utils.transport)
                    packers.Bool.pack(b, _self.utils.transport)
                return _self.utils.get_reply(seq)
            def sync_900118(_self, _proxy, a, b):
                with _self.utils.invocation(900118, packers.Int32) as seq:
                    ClassBObjRef.pack(_proxy, _self.utils.transport)
                    packers.Str.pack(a, _self.utils.transport)
                    packers.Bool.pack(b, _self.utils.transport)
                return _self.utils.get_reply(seq)
            def sync_900147(_self, _proxy):
                with _self.utils.invocation(900147, None) as seq:
                    PersonObjRef.pack(_proxy, _self.utils.transport)
                return _self.utils.get_reply(seq)
            def sync_900110(_self, _proxy, value):
                with _self.utils.invocation(900110, None) as seq:
                    ClassAObjRef.pack(_proxy, _self.utils.transport)
                    packers.Int32.pack(value, _self.utils.transport)
                return _self.utils.get_reply(seq)
            def sync_900112(_self, _proxy, value):
                with _self.utils.invocation(900112, None) as seq:
                    ClassAObjRef.pack(_proxy, _self.utils.transport)
                    packers.Int32.pack(value, _self.utils.transport)
                return _self.utils.get_reply(seq)
            def sync_900098(_self, ):
                with _self.utils.invocation(900098, _list_ClassC) as seq:
                    pass
                return _self.utils.get_reply(seq)
            def sync_900073(_self, a, b, c, d, e, f, g, h, i, j, k, l, m, n):
                with _self.utils.invocation(900073, EverythingPacker) as seq:
                    packers.Int8.pack(a, _self.utils.transport)
                    packers.Int16.pack(b, _self.utils.transport)
                    packers.Int32.pack(c, _self.utils.transport)
                    packers.Int64.pack(d, _self.utils.transport)
                    packers.Float.pack(e, _self.utils.transport)
                    packers.Bool.pack(f, _self.utils.transport)
                    packers.Date.pack(g, _self.utils.transport)
                    packers.Buffer.pack(h, _self.utils.transport)
                    packers.Str.pack(i, _self.utils.transport)
                    _list_float.pack(j, _self.utils.transport)
                    _set_int32.pack(k, _self.utils.transport)
                    _map_int32_str.pack(l, _self.utils.transport)
                    AddressPacker.pack(m, _self.utils.transport)
                    PersonObjRef.pack(n, _self.utils.transport)
                return _self.utils.get_reply(seq)
            def sync_900142(_self, _proxy):
                with _self.utils.invocation(900142, PersonObjRef) as seq:
                    PersonObjRef.pack(_proxy, _self.utils.transport)
                return _self.utils.get_reply(seq)
            def sync_900134(_self, _proxy):
                with _self.utils.invocation(900134, packers.Str) as seq:
                    PersonObjRef.pack(_proxy, _self.utils.transport)
                return _self.utils.get_reply(seq)
            def sync_900131(_self, _proxy):
                with _self.utils.invocation(900131, _list_ClassA) as seq:
                    ClassCObjRef.pack(_proxy, _self.utils.transport)
                return _self.utils.get_reply(seq)
            def sync_900124(_self, _proxy):
                with _self.utils.invocation(900124, packers.Int32) as seq:
                    ClassCObjRef.pack(_proxy, _self.utils.transport)
                return _self.utils.get_reply(seq)
            def sync_900126(_self, _proxy):
                with _self.utils.invocation(900126, packers.Float) as seq:
                    ClassCObjRef.pack(_proxy, _self.utils.transport)
                return _self.utils.get_reply(seq)
            def sync_900122(_self, _proxy):
                with _self.utils.invocation(900122, packers.Int32) as seq:
                    ClassCObjRef.pack(_proxy, _self.utils.transport)
                return _self.utils.get_reply(seq)
            def sync_900119(_self, _proxy):
                with _self.utils.invocation(900119, packers.Float) as seq:
                    ClassBObjRef.pack(_proxy, _self.utils.transport)
                return _self.utils.get_reply(seq)
            def sync_900116(_self, _proxy):
                with _self.utils.invocation(900116, packers.Int32) as seq:
                    ClassBObjRef.pack(_proxy, _self.utils.transport)
                return _self.utils.get_reply(seq)
            def sync_900114(_self, _proxy):
                with _self.utils.invocation(900114, packers.Int32) as seq:
                    ClassBObjRef.pack(_proxy, _self.utils.transport)
                return _self.utils.get_reply(seq)
            def sync_900144(_self, _proxy):
                with _self.utils.invocation(900144, PersonObjRef) as seq:
                    PersonObjRef.pack(_proxy, _self.utils.transport)
                return _self.utils.get_reply(seq)
            def sync_900139(_self, _proxy, value):
                with _self.utils.invocation(900139, None) as seq:
                    PersonObjRef.pack(_proxy, _self.utils.transport)
                    AddressPacker.pack(value, _self.utils.transport)
                return _self.utils.get_reply(seq)
            def sync_900104(_self, ):
                with _self.utils.invocation(900104, RecordBPacker) as seq:
                    pass
                return _self.utils.get_reply(seq)
            def sync_900146(_self, _proxy, partner):
                with _self.utils.invocation(900146, None) as seq:
                    PersonObjRef.pack(_proxy, _self.utils.transport)
                    PersonObjRef.pack(partner, _self.utils.transport)
                return _self.utils.get_reply(seq)
            def sync_900133(_self, _proxy, a, b):
                with _self.utils.invocation(900133, packers.Int32) as seq:
                    ClassCObjRef.pack(_proxy, _self.utils.transport)
                    packers.Str.pack(a, _self.utils.transport)
                    packers.Bool.pack(b, _self.utils.transport)
                return _self.utils.get_reply(seq)
            def sync_900129(_self, _proxy, a, b):
                with _self.utils.invocation(900129, packers.Int32) as seq:
                    ClassCObjRef.pack(_proxy, _self.utils.transport)
                    packers.Str.pack(a, _self.utils.transport)
                    packers.Bool.pack(b, _self.utils.transport)
                return _self.utils.get_reply(seq)
            def sync_900128(_self, _proxy, a, b):
                with _self.utils.invocation(900128, packers.Int32) as seq:
                    ClassCObjRef.pack(_proxy, _self.utils.transport)
                    packers.Str.pack(a, _self.utils.transport)
                    packers.Bool.pack(b, _self.utils.transport)
                return _self.utils.get_reply(seq)
            def sync_900043(_self, name, father, mother):
                with _self.utils.invocation(900043, PersonObjRef) as seq:
                    packers.Str.pack(name, _self.utils.transport)
                    PersonObjRef.pack(father, _self.utils.transport)
                    PersonObjRef.pack(mother, _self.utils.transport)
                return _self.utils.get_reply(seq)
        
        self._funcs = Functions(self._utils)
        
        self.Person = agnos.Namespace()
        self.Person['init'] = self._funcs.sync_900043
    
    def get_class_c(_self, ):
        return _self._funcs.sync_900098()
    def func_of_everything(_self, a, b, c, d, e, f, g, h, i, j, k, l, m, n):
        return _self._funcs.sync_900073(a, b, c, d, e, f, g, h, i, j, k, l, m, n)
    def get_record_b(_self, ):
        return _self._funcs.sync_900104()
    
    def assert_service_compatibility(self):
        info = self.get_service_info(agnos.INFO_GENERAL)
        if info["AGNOS_PROTOCOL_VERSION"] != AGNOS_PROTOCOL_VERSION:
            raise agnos.WrongAgnosVersion("expected protocol '%s' found '%s'" % (AGNOS_PROTOCOL_VERSION, info["AGNOS_PROTOCOL_VERSION"]))
        if info["SERVICE_NAME"] != "FeatureTest":
            raise agnos.WrongServiceName("expected service 'FeatureTest', found '%s'" % (info["SERVICE_NAME"],))
        if CLIENT_VERSION:
            supported_versions = info.get("SUPPORTED_VERSIONS", None)
            if not supported_versions or CLIENT_VERSION not in supported_versions:
                raise agnos.IncompatibleServiceVersion("server does not support client version '%s'" % (CLIENT_VERSION,))
