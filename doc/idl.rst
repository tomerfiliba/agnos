.. highlight:: xml

Agnos IDL
=========
Instead of creating a domain-specific language, Agnos uses a simple XML document 
for specifying the IDL (*interface definition language*), the semantics of which 
are very trivial (no need for schemas/DTD).

The root element is ``<service>``, and within it reside ``<typedef>`` s, ``<const>`` s,
``<enum>`` s, ``<function>`` s, ``<record>`` s, ``<exception>`` s and ``<class>`` es.

.. note::
  Documentation can be added to any element in the XML document. This is done by 
  either providing a ``doc`` attribute, or a ``<doc>`` sub-element, but not both 
  at the same time, of course. For example::
  
    <record name="foo">
        <doc>this record represents foo data</doc>
        <attr name="bar" type="int32" doc="bar must be an even number" />
    </record>

.. note::
  An ``id`` attribute can be supplied to every element, to set its internal ID. 
  This ID number must be unique throughout the file. If not given, an auto-generated
  ID will be used ::
  
    <func name="spam" type="string" id="1337">
        <arg name="bacon" type="int64" />
        <arg name="eggs" type="int16" />
    </func>

.. note::
  An ``<annotation>`` element can be placed inside every IDL element. 
  Annotations must have ``name`` and ``value`` attributes, which are free-form 
  strings, and can be used to embed additional programmatic information into
  the IDL. For example::
  
    <func name="mount" type="void">
        <arg name="dev" type="string" />
        <arg name="path" type="string" />
        <annotation name="user" value="john" />
    </func>

  The annotation itself is meaningless to the Agnos compiler, but the service 
  implementation may be aware of it, and make sure that only ``john`` 
  calls this function.


IDL Elements
============

.. _idl-service:

<service>
---------

Attributes 
^^^^^^^^^^

* ``name`` (required) - the name of the service. For example: ``name = "foobar"``.

* ``package`` (optional) - the package of the service. 
  For example: ``package = "org.eclipse.spam"`` . Note that the semantics depend 
  on the language, e.g., in ``java`` it will create the necessary directory structure, 
  while in ``C#`` it will only use ``namespace`` s.

* ``versions`` (optional) - a comma-separated list of versions (strings) provided 
  by the service. For example, ``versions="1.0, 1.1-beta, 1.1"`` -- this means 
  the service supports versions "1.0", "1.1-beta", and "1.1". When adding new 
  versions, always append them at the end, e.g., ``versions="1.0, 1.1-beta, 1.1, 1.2"``.

  .. note::
     A client may want to check its compatibility with the service's supported versions.
     This is done by the ``assertServiceCompatibiliy()`` function of ``Client`` objects.

* ``clientversion`` (optional) - a string specifying the client's version. 
  If not specified, the last element of the server's version is assumed to be 
  the latest version, and is thus used as the client version.

Contained Elements
^^^^^^^^^^^^^^^^^^

``typedef``, ``enum``. ``const``, ``record``, ``exception``, ``class``, ``function``

.. _idl-typedef:

<typedef>
---------

Attributes
^^^^^^^^^^

* ``name`` (required) - the name of the new type

* ``type`` (required) - the name of the existing type

Example 
^^^^^^^
::

  <typedef name="size_t" type="int32" />

.. _idl-enum:

<enum>
------

Attributes
^^^^^^^^^^

* ``name`` (required) - the name of the enum.

Contained Elements
^^^^^^^^^^^^^^^^^^

* ``member``

  * ``name`` (required) - the name of the enum member
  
  * ``value`` (optional) - an integer value serving as the value of the enum member. 
    If not supplied, the value is one more than the previous member's value, 
    and the first member defaults to zero.

Example 
^^^^^^^
::
  
  <enum name="filesystems">
      <member name="FAT12" value="17" />
      <member name="FAT16" />
      <member name="FAT32" />
      <member name="NTFS" value="33" />
  </enum>

.. _idl-const:

<const>
-------

Attributes
^^^^^^^^^^

* ``name`` (required) - the name of the constant

* ``type`` (required) - the type of the constant

* ``value`` (required) - the value of the constant

Example 
^^^^^^^
::

  <const name="pi" type="float" value="3.1415926535" />

.. _idl-record:

<record>
--------

Records are much like ``struct``s in ``C``: a collection of named fields. 
They are //by-value// objects, meaning they are copied by-value to the other 
side, when sent over the wire.

Attributes
^^^^^^^^^^

* ``name`` (required) - the name of the record.

* ``extends`` (optional) - a comma-separated list of previously-defined records, 
  which this record extends. This **should not** be confused with the object-oriented 
  notion of inheritance -- when record B extends record A, it only means that 
  B "automatically" defines all the fields of A. Note that only records can be 
  specified in this list, not classes or any other type.

Contained Elements
^^^^^^^^^^^^^^^^^^

* ``attr``

  * ``name`` (required) - the name of the record's attribute ("field")

  * ``type`` (required) - the type of the attribute

Example 
^^^^^^^
::

  <record name="Address">
      <attr name="country" type="string" />
      <attr name="city" type="string" />
      <attr name="street" type="string" />
      <attr name="number" type="int32" />
  </record>

.. _idl-exception:

<exception>
-----------
An exception is basically a record, only it derives from the proper exception 
base-class for the language. It is basically a synonym for "record", and 
inherits all of its semantics.

Example 
^^^^^^^
::

  <exception name="InvalidAddress">
      <attr name="error_code" type="int32" />
      <attr name="error_text" type="string" />
  </exception>


.. _idl-class:

<class>
----------

Classes, unlike records, are passed //by-reference//. In this scheme, 
the actual object "lives" on the server, and is recreated on the client as a 
`proxy object <http://en.wikipedia.org/wiki/Proxy_pattern>`_ , with the same 
"looks and feel". Any operation performed on the proxy object is "transferred" 
to the server, and gets carried out on the actual object.

Attributes
^^^^^^^^^^

* ``name`` (required) - the name of the class

* ``extends`` (optional) - a comma-separated list of previously defined classes. 

Contained Elements
^^^^^^^^^^^^^^^^^^

<attr>
""""""

* ``name`` (required) - the name of the attribute ("property" or "field")

* ``type`` (required) - the type of the attribute

* ``get`` (optional) - a boolean (``"yes"/"no"`` or ``"true"/"false"``) indicating whether this attribute has **read access**. Default is "yes".

* ``set`` (optional) - a boolean (``"yes"/"no"`` or ``"true"/"false"``) indicating whether this attribute has **write access**. Default is "yes".

<method>
""""""""

* ``name`` (required) - the name of the method

* ``type`` (required) - the return type of the method

* ``<arg>`` - specify an argument of the method

  * ``name`` (required) - the name of the method's argument

  * ``type`` (required) - the type of the method's argument

Example 
^^^^^^^
::

  <class name="Person">
      <attr name="full_name" type="string" />
      <attr name="address" type="Address" />
      <attr name="id" type="int32" set="no" />
  
      <method name="marry" type="void">
          <arg name="spouse" type="Person">
      </method>
  
      <method name="give_birth" type="Person">
          <arg name="full_name" type="string">
      </method>
  
      <method name="get_children" type="list[Person]" />
  </class>


.. _idl-function:

<function>
----------

Functions are the most fundamental element of RPC: they take arguments, perform an operation, and may return a result. 
Note: ``<func>`` is a synonym.

Attributes
^^^^^^^^^^

* ``name`` (required) - the name of the function.

* ``type`` (required) - the return type of this function; may be ``void``

Contained Elements
^^^^^^^^^^^^^^^^^^

<arg>
"""""

Specify an argument of the function:

* ``name`` (required) - the name of the function's argument

* ``type`` (required) - the type of the function's argument

Example 
^^^^^^^
::

  <function name="mount" type="void">
      <arg name="dev" type="string" />
      <arg name="path" type="string" />
  </function>

.. _idl-types:

IDL Types
=========

Simple data types
------------------

* ``bool`` - a boolean value (``true``/``false``)
* ``int8``, ``int16``, ``int32`` (also ``int``), ``int64`` - an 8, 16, 
  32, or 64-bit **signed integer**
* ``float`` - a 64-bit floating point number (usually referred to as ``double`` 
  most programming languages)
* ``string`` (also ``str``) - a Unicode string (UTF-8 encoded)
* ``buffer`` - a buffer of raw bytes
* ``date`` - a date-time value, representing a point in time. It represents the 
  number of microseconds since January 1st, 0001 under UTC. Note: on some systems 
  and targets, the range is different. For instance, on ``java`` is can 
  represent dates starting from January 1st, 1970.

Containers
----------
* ``list[X]`` - an ordered collection ("list") of elements of type ``X``. 
  For example: ``list[int32]``

* ``set[X]`` - an unordered collection of unique elements ("set") of type ``X``. 
  For example: ``set[string]``

* ``map[X, Y]`` (also ``dict[X, Y]``) - an unordered mapping of unique elements 
  of type ``X`` ("keys") to elements of type ``Y`` ("values"). The keys in 
  the map are unique, and are mapped to a single value. The values are not 
  required to be unique. For example: ``map[dates, string]``

* ``heteromap`` (also ``heterodict``) - a heterogeneous map, meaning it is not
  limited to keys or values of a certain, predetermined type. Note that on ``C++``,
  only the simple data types (listed above) can be used as **keys**. 
  This is a limitation of ``std::map`` type.

Void
----
``void`` can be used only as the type of **functions** and **methods** that do 
not return anything.

Reserved Names
==============

* The IDL may not define a type named as a built-in type, or a previously defined type. 
  For instance, ``<typedef name="float" type="int32" />`` is invalid.

* All names in the IDL **may not begin with an underscore** (``"_"``). For instance, 
  ``<func name="_foo" type="void" />`` is invalid.

