Protocol Specification
======================
This section describes the wire-format Agnos uses to encode values, and serves
as a reference for new implementations of ``libagnos`` (for other languages).
Note that the ``java`` implementation of ``libagnos`` is the "reference 
implementation". Refer to :doc:`types` for more information on types.

.. note::
  Some notes of notations:
  
  * All sizes are in units of bytes, unless stated otherwise. 

  * Byte layout is surrounded by bracked (``[]``), ordered from left to right,
    and each byte is delimited by spaces. Byte values are given in hexadecimal 
    form. For example, ``[12 34 56]`` means three bytes: the first 0x12, 
    followed by 0x34, and 0x56 comes last.


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

Payload
-------
If the message is sent by the client (a request), the first byte is the 
command code (see below), and it is followed by the command's payload.

If the message is sent by the server (a reply), the first byte is the reply
code (see below), and it is followed by the reply's payload

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

================  =======
Query             Value
================  =======
INFO_META         0
INFO_SERVICE      1
INFO_FUNCTIONS    2
INFO_REFLECTION   3
================  =======



Data Serialization
==================

``int8``
--------
* Size: 1 byte
* Packer ID: 1
* Layout: Signed integer
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
* Layout: Signed integer, big-endian byte order
* Example: ``[2F 8A]`` encodes the decimal value 12170

``int32``
---------
* Size: 4 bytes
* Packer ID: 4
* Layout: Signed integer, big-endian byte order
* Example: ``[11 55 2F 8A]`` encodes the decimal value 290795402

``int64``
---------
* Size: 8 bytes
* Packer ID: 5
* Layout: Signed integer, big-endian byte order
* Example: ``[00 00 23 5C 11 55 2F 8A]`` encodes the decimal value 38878334758794

``float``
---------
* Size: 8 bytes
* Packer ID: 6
* Layout: IEEE-754 64-bit floating point number, big-endian byte order
* Example: ``[18 2d 44 54 fb 21 09 40]`` encodes the decimal value 3.1415926535897931

``date``
--------
* Size: 8 bytes

* Packer ID: 8

* Layout: The number of microseconds since 00:00:00, January 1st, 0000, UTC.
  The number is encoded as an ``int64``.

* Example: ``[00 dc bf fd 52 04 78 00]`` represents 00:00:00, January 1st, 1970, UTC.
  ``[00 e1 5d 59 de d8 ed dd]`` represents 17:18:52 February 28th, 2011, UTC.

``buffer``
----------
* Size: 4+

* Packer ID: 7

* Layout: 4 bytes length specifier (in ``int32`` structure), followed by that 
  many bytes

* Example: ``[00 00 00 05 68 65 6c 6c 6f]`` encodes the buffer 
  ``byte[] buf = {0x68, 0x65, 0x6c, 0x6c, 0x6f}``

``str``
---------
* Size: 4+

* Packer ID: 9

* Layout: 4 bytes length specifier (in ``int32`` structure), followed by
  that many bytes encoded in UTF8.

* Example: ``[00 00 00 05 68 65 6c 6c 6f]`` encodes the UTF8 string ``"hello"``

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

* Layout: 4 bytes length specifier (in ``int32`` structure), followed by
  that many instances of ``T``.

* Examples:

  * ``list[int32]``: ``[00 00 00 02 11 22 33 44 55 66 77 88]`` encodes
    ``int arr[] = {0x11223344, 0x55667788}``

  * ``list[str]``: ``[00 00 00 02 00 00 00 01 41 00 00 00 02 42 43]`` encodes 
    ``string arr[] = {"A", "BC"}``


``set[T]``
-----------
To do


``map[K,V]``
------------
To do



``heteromap``
-------------
To do












