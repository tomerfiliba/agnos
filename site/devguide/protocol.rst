.. _doc-protocol:

Protocol Specification
======================
This section describes the wire-format Agnos uses to encode values, and serves
as a reference for new implementations of ``libagnos`` (for other languages).
Note that the ``java`` implementation of ``libagnos`` is the "reference 
implementation". Refer to :ref:`doc-types` for more information on types.

.. note::
  Some notes of notations:
  
  * All sizes are in units of bytes, unless stated otherwise. 

  * Byte layout is surrounded by brackets (``[]``), ordered from left to right,
    and each byte is delimited by spaces. Byte values are given in hexadecimal 
    form. For example, ``[12 34 56]`` means three bytes: the first 0x12, 
    followed by 0x34, and 0x56 comes last.
    
  * Dots are sometimes placed inside byte-layouts, such as ``[00 00 00 02 . 41 42]``,
    to denote the boundaries of different values (they have no semantic meaning).


The Protocol
============

The protocol is very simple, and is made of messages. Each message consists of
a header, followed by the payload.

Message Header
--------------

======  ================================  ===============
Order   Description                       Size (bytes)
======  ================================  ===============
1       Sequence number                   4 (``int32``)
2       Message length (in bytes)         4 (``int32``) 
3       Uncompressed length (in bytes)    4 (``int32``)
======  ================================  ===============

Note on Compression
^^^^^^^^^^^^^^^^^^^
If the uncompressed length is 0, it means the message has not been compressed
and thus no decompression should take place -- the "on-the-wire" length 
(second integer in the header) is also the actual length. In this case, you 
can continue processing the payload as-is.

If this field is greater than 0, the message has been compressed. The "on-the-wire"
length denotes the compressed size (number of bytes over-the-wire), while
the uncompressed length denotes the original size of the message, before 
compression. In this case, you have to decompress the payload, prior to continuing 
its processing.

Agnos uses the free and widely-available `DEFLATE <http://en.wikipedia.org/wiki/DEFLATE>`_
algorithm for compression (as implemented by `zlib <http://zlib.net/>`_).


Payload
-------
If the message is sent by the client (a **request**), the first byte is the 
command code (see below), followed by the command's payload.

If the message is sent by the server (a **reply**), the first byte is the reply
code (see below), followed by the reply's payload.


Constants
---------

Commands
^^^^^^^^
====================  ========
Command               Value
====================  ========
CMD_PING              0
CMD_INVOKE            1
CMD_QUIT              2
CMD_DECREF            3
CMD_INCREF            4
CMD_GETINFO           5
CMD_CHECK_CAST        6
CMD_QUERY_PROXY_TYPE  7
====================  ========

Reply Codes
^^^^^^^^^^^
=======================  ========
Reply                    Value
=======================  ========
REPLY_SUCCESS            0
REPLY_PROTOCOL_ERROR     1
REPLY_PACKED_EXCEPTION   2
REPLY_GENERIC_EXCEPTION  3
=======================  ========

Info Codes
^^^^^^^^^^
These codes are used when a client calls ``getServiceInfo()``:

================  =======  =================================================
Query             Value    Description
================  =======  =================================================
INFO_META         0        Queries meta information, i.e., the ``INFO_XXX``
                           codes that the server supports
INFO_SERVICE      1        Queries information about the service (name, 
                           version, IDL digest, etc)
INFO_FUNCTIONS    2        Queries information about the functions exposed
                           by the service (function names, argument types
                           and return types)
INFO_REFLECTION   3        Queries reflection information about the service,
                           which includes pretty much everything found in
                           the IDL file (classes, constants, enums, records,
                           and functions)
================  =======  =================================================

Data Serialization
==================

``int8``
--------
* Size: 1 byte
* Packer ID: 1
* Layout: *Signed* integer
* Example: ``[8A]`` encodes the decimal value -118

``bool``
--------
* Size: 1 byte
* Packer ID: 2
* Layout: N/A. The value 0 means ``false``, any other (nonzero) value means ``true``
* Example: ``[03]`` encodes the boolean value ``true``

``int16``
---------
* Size: 2 bytes
* Packer ID: 3
* Layout: *Signed* integer, *big-endian* byte order
* Example: ``[2F 8A]`` encodes the decimal value 12170

``int32``
---------
* Size: 4 bytes
* Packer ID: 4
* Layout: *Signed* integer, *big-endian* byte order
* Example: ``[11 55 2F 8A]`` encodes the decimal value 290795402

``int64``
---------
* Size: 8 bytes
* Packer ID: 5
* Layout: *Signed* integer, *big-endian* byte order
* Example: ``[00 00 23 5C 11 55 2F 8A]`` encodes the decimal value 38878334758794

``float``
---------
* Size: 8 bytes
* Packer ID: 6
* Layout: IEEE-754 64-bit floating point number, **big-endian** byte order
* Example: ``[18 2d 44 54 FB 21 09 40]`` encodes the decimal value 3.1415926535897931

``date``
--------
* Size: 8 bytes

* Packer ID: 8

* Layout: The number of *microseconds* since 00:00:00, January 1st, 0000, UTC.
  The number is encoded as an ``int64``.

* Example: ``[00 dc bf fd 52 04 78 00]`` represents ``00:00:00, January 1st, 1970, UTC``.
  ``[00 e1 5d 59 de d8 ed dd]`` represents ``17:18:52 February 28th, 2011, UTC``.

``buffer``
----------
* Size: 4+

* Packer ID: 7

* Layout: 4 bytes length specifier (in ``int32`` format), followed by that 
  many **bytes**

* Example: ``[00 00 00 05 . 68 65 6c 6c 6f]`` encodes the buffer 
  ``byte[] buf = {0x68, 0x65, 0x6c, 0x6c, 0x6f}``

``str``
---------
* Size: 4+

* Packer ID: 9

* Layout: 4 bytes length specifier (in ``int32`` format), followed by
  that many **bytes encoded in UTF8**. The sequence of bytes is then UTF8-decoded
  to produce the string.

* Example: ``[00 00 00 05 . 68 65 6C 6C 6F]`` encodes the UTF8 string ``"hello"``

``list[T]``
-----------
* Size: 4+

* Packer ID: Varies for every ``T``. The following types have predefined IDs:

  ================  ====
  Type              ID
  ================  ====
  ``list[int8]``    800 
  ``list[bool]``    801 
  ``list[int16]``   802 
  ``list[int32]``   803 
  ``list[int64]``   804 
  ``list[float]``   805 
  ``list[buffer]``  806 
  ``list[date]``    807 
  ``list[str]``     808
  ================  ==== 

* Layout: 4 bytes length specifier (in ``int32`` format), followed by
  that many instances of ``T``.

* Examples:

  * ``list[int32]``: ``[00 00 00 02 . 11 22 33 44 . 55 66 77 88]`` encodes
    ``int arr[] = {0x11223344, 0x55667788}``

  * ``list[str]``: ``[00 00 00 02 . 00 00 00 01 . 41 00 00 00 02 42 43]`` encodes 
    ``String arr[] = {"A", "BC"}``


``set[T]``
-----------
* Size: 4+

* Packer ID: Varies for every ``T``. The following types have predefined IDs:

  ================  ====
  Type              ID
  ================  ====
  ``set[int8]``     820 
  ``set[bool]``     821 
  ``set[int16]``    822 
  ``set[int32]``    823 
  ``set[int64]``    824 
  ``set[float]``    825 
  ``set[buffer]``   826 
  ``set[date]``     827 
  ``set[str]``      828
  ================  ==== 

* Layout: 4 bytes length specifier (in ``int32`` format), followed by
  that many instances of ``T``.

* Examples:

  * ``set[int32]``: ``[00 00 00 02 . 11 22 33 44 . 55 66 77 88]`` encodes
    ``Set<Integer> myset = new HashSet<Integer>(); 
    myset.add(0x11223344); myset.add(0x55667788);``

  * ``set[str]``: ``[00 00 00 02 . 00 00 00 01 . 41 . 00 00 00 02 . 42 43]`` encodes 
    ``Set<String> myset = new HashSet<String>(); myset.add("A"); myset.add("BC");``


``map[K,V]``
------------
* Size: 4+

* Packer ID: Varies for every ``K`` and ``V``. The following types have predefined IDs:

  ======================  ====
  Type                    ID
  ======================  ====
  ``map[int32, int32]``   850 
  ``map[int32, str]``     851 
  ``map[str, int32]``     852 
  ``map[str, str]``       853 
  ======================  ==== 

* Layout: 4 bytes length specifier (in ``int32`` format), followed by
  that many instances of ``K``-and-``V`` pairs.

* Examples:

  * ``map[int32, str]``: ``[00 00 00 02 . 11 22 33 44 . 00 00 00 05 . 
    68 65 6C 6C 6F 22 33 44 55 . 00 00 00 02 . 41 42]`` 
    encodes ``Map<Integer, String> mymap = new HashMap<Integer, String>(); 
    mymap.put(0x11223344, "hello"); mymap.put(0x22334455, "AB");``

  * ``set[str]``: ``[00 00 00 02 . 00 00 00 01 . 41 . 00 00 00 02 . 42 43]`` encodes 
    ``Set<String> myset = new HashSet<String>(); myset.add("A"); myset.add("BC");``


``heteromap``
-------------
* Size: 4+

* Packer ID:
 
  * The builtin-packer has an ID of 998 (defined in libagnos)
  * The generated packer has an ID of 999 (defined in the generated bindings)

* Layout: 4 bytes length specifier (in ``int32`` format), followed by
  that many instances of ``(key-packer-id, key, value-packer-id, value)``:
  each item is a key-value pair that also stores a key-packer and
  a value-packer (denoted by their packer IDs as ``int32``).

* Example: ``[00 00 00 02 . 00 00 00 09 . 00 00 00 04 . 6E 61 6D 65 .
  00 00 00 09 . 00 00 00 04 . 4A 6f 68 6E . 00 00 00 09 . 00 00 00 03 . 
  61 67 65 . 00 00 00 04 . 00 00 00 2A]``. For convenience, here's the
  data structure parsed::

      00 00 00 02                               # number of items
       
        # first item
        00 00 00 09                             # key packer ID (String) 
          00 00 00 04 . 6E 61 6D 65             # key
        00 00 00 09                             # value packer id (String)
          00 00 00 04 . 4A 6f 68 6E             # value
         
        # second item
        00 00 00 09                             # key packer ID (String)
          00 00 00 03 . 61 67 65                # key
        00 00 00 04                             # value packer ID (Int32)
          00 00 00 2A                           # value
  
  which encodes
  
  .. code-block:: java
  
    HeteroMap h = new HeteroMap();
    h.put("name", "John");
    h.put("age", 42);


Reference Session
=================

In this section we'll examine a "captured" session between an Agnos client 
and an Agnos server. The session was generated by capturing the transport
of the python unit-test.

Request (1)
-----------
In this part, the client attempts to invoke a remote function, whose signature is

.. code-block:: java

    PersonProxy createPerson(String name, PersonProxy father, PersonProxy mother);

The code the client executes is

.. code-block:: java

    PersonProxy eve = createPerson("eve", null, null);

Client sends: ``[00 00 00 04 . 00 00 00 1c . 00 00 00 00 . 01 . 00 0d bb cb . 
00 00 00 03 . 65 76 65 . ff ff ff ff ff ff ff ff . ff ff ff ff ff ff ff ff]``

Header:

* ``[00 00 00 04]`` - message sequence number
* ``[00 00 00 1C]`` - message length (28 bytes)
* ``[00 00 00 00]`` - uncompressed message length. 0 means no decompression is needed.

Payload:

* ``[01]`` - command code (``CMD_INVOKE`` -- invoke a function) 
* ``[00 0d bb cb]`` - function ID (900043)

Following are the function's arguments:

* ``[00 00 00 03 . 65 76 65]`` - the string ``"eve"``
* ``[ff ff ff ff ff ff ff ff]`` - object reference (``int64``). 
  (-1) indicates ``null``.
* ``[ff ff ff ff ff ff ff ff]`` - object reference (``int64``). 
  (-1) indicates ``null``.

Response
^^^^^^^^
Server sends in response: ``[00 00 00 04 . 00 00 00 09 . 00 00 00 00 . 00 . 
00 00 00 00 09 7a 85 8c]``

Header:

* ``[00 00 00 04]`` - message sequence number (copied from the request)
* ``[00 00 00 09]`` - message length (9 bytes)
* ``[00 00 00 00]`` - uncompressed message length. 0 means no decompression is needed.

Payload:

* ``[00]`` - reply code (``REPLY_SUCCESS`` - success) 
* ``[00 00 00 00 09 7a 85 8c]`` - object reference (int64). The client will create a
  ``PersonProxy`` instance referencing the remote object through this unique number.

Request (2)
-----------
The client created a second person (``adam``), and now it attempts to marry
the two, with the following code

.. code-block:: java
    
    eve.marry(adam);

Client sends: ``[00 00 00 06 . 00 00 00 15 . 00 00 00 00 . 01 . 00 0d bc 32 . 
00 00 00 00 09 7a 85 8c . 00 00 00 00 09 7a 86 6c]``

The sequence number is 6, followed by the message length (21), and no compression
is used (0). The command code is ``CMD_INVOKE``, followed by the function ID
(900146), and it's arguments: ``[00 00 00 00 09 7a 85 8c]`` and 
``[00 00 00 00 09 7a 86 6c]``. 

The first argument is the ``this`` or ``self`` instance of the method ``marry()``,
and in our case, it's ``eve``'s reference number. The second argument is ``adam``'s 
reference number.

Reply
^^^^^
Server sends: ``[00 00 00 06 . 00 00 00 01 . 00 00 00 00 . 00]``

The sequence number is 6, followed by the message length (1), and no compression
is used. The reply code is REPLY_SUCCESS, and this is it -- the method's return
type is ``void``.

Request (3)
-----------
Now the client attempts to invoke

.. code-block:: java
    
    adam.marry(eve);
 
But ``adam`` is is already married. This will result in an exception. 

Client sends: ``[00 00 00 09 . 00 00 00 15 . 00 00 00 00 . 01 . 00 0d bc 32 . 
00 00 00 00 09 7a 86 6c . 00 00 00 00 09 7a 85 8c]``

Reply
^^^^^
The service implementation throws an exception, as it does not allow for persons
to be re-married.
 
Server sends: ``[00 00 00 09 . 00 00 00 20 . 00 00 00 00 . 02 . 00 0d bb ae . 
00 00 00 0f . 61 6c 72 65 61 64 79 20 6d 61 72 72 69 65 64 . 00 00 00 00 09 7a 86 6c]``

The sequence number is 9, followed by the message length (32), and no compression
is used. The reply code is ``REPLY_PACKED_EXCEPTION``, which indicates that a 
packed-exception follows. The exception class ID is 900014 (``MartialStatusError``
in this case), whose constructor takes ``String message`` (a description of the 
error) and ``PersonProxy person`` (indicates the person who's already married).

So here the exception message is ``"already married"``, and the "offending" person
is ``adam`` (it his reference number that's returned).







