import itertools

try:
    next
except NameError:
    def next(iterator):
        return iterator.next()

try:
    itertools.count.next
except AttributeError:
    class icount(object):
        __slots__ = ["_count"]
        def __init__(self, val = 0):
            self._count = itertools.count(val)
        def __str__(self):
            return str(self._count)
        def __next__(self):
            return next(self._count)
        next = __next__
else:
    icount = itertools.count



