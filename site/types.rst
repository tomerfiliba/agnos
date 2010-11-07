Data Types
==========

Agnos defines the following **primitive types**. Note that these types, 
including their aliases, are **reserved names** -- you may not define your own 
type, overriding any of these names. 

**Value types** are passed by-value, meaning, serialized to bytes and sent over 
the wire. This means that a copy of the original object is created on the other
side.

This is unlike **reference types**, which are passed by-reference. For reference
types, only a unique identifier is sent over the wire, while the actual object
remains where it is.


Simple Types
------------
.. note::
  These are all value types

* ``bool`` -- a boolean value: one of ``true`` or ``false``.
* ``int8`` -- signed integer, 8 bits wide (-128..127).
* ``int16`` -- signed integer, 16 bits wide (-32768..32767).
* ``int32`` or ``int`` -- signed integer, 32 bits wide (-2^31..2^31-1).
* ``int64`` -- signed integer, 64 bits wide (-2^63..2^63-1).
* ``float`` -- 64-bit floating point number (usually called ``double``).
* ``datetime`` -- a point in time, in microsecond resolution. It represents the 
  number of microseconds from 00:00:00, January 1st, year 0 in UTC; however, its
  actual range is limited by the implementation:
  
  * In ``java`` it can only represent dates after January 1st, 1970 
    (limitation of ``java.util.Date``).
  * In ``C++``, it can only represent dates after January 1st, 1400 
    (limitation of ``boost::posix_time::ptime``).
  * In ``python`` and ``C#``, it has the full range (starting from year 0 
    through 9999).

* ``string`` or ``str`` -- a unicode string (UTF8 encoded).
* ``buffer`` -- a binary buffer (array of bytes), useful for passing binary data
  blobs.

By-Value Containers
-------------------
.. note::
  These are all value types

* ``list[V]`` -- a list (also vector) of elements of type ``V``. 
  Example usage: ``list[int32]``.

* ``set[V]`` -- a set (unordered collection) of unique elements of type ``V``.
  Example usage: ``set[float]``.

* ``map[K, V]`` or ``dict[K, V]`` -- a map of unique keys of type ``K`` to 
  values of type ``V``. Example usage: ``map[datetime, string]``. 

* ``heteromap`` or ``heterodict`` -- a heterogenous map, meaning a map contains 
  keys of any type and values of any type.
  
  * In ``C++``, the keys are limited only to the simple types (listed above);
    this is because STL implementation requires well-ordering on the keys.
    Values are unrestricted.

Containers are not limited to holding simple types only; for instance, 
``map[int, set[str]]`` is a valid type.

Void
----
``void`` is also a quasi-type, that can only appear as the return type of 
functions and methods; it is invalid in all other contexts. The name ``void`` 
is a reserved name as well.

By-Reference Collections
------------------------
These are the by-reference counterparts of the by-value collections listed above.

.. note::
   THESE TYPES ARE NOT IMPLEMENTED IN VERSION 1.0. They are only given here 
   because these names are reserved for future use.

* ``reflist[V]`` -- To be implemented in a future version
* ``refset[V]`` -- To be implemented in a future version
* ``refmapp[K, V]`` or ``refdict[K, V]`` -- To be implemented in a future version




