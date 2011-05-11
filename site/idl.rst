IDL
===

Agnos processes an 
`Interface Description Language (IDL) <http://en.wikipedia.org/wiki/Interface_description_language>`_
specification of a service, and generates target-language bindings. 
This IDL is written as a very simple **XML document**, the semantics of which 
are discussed here.

Before reading this, be sure to read the :doc:`concepts` and :doc:`types`.

The root element of every IDL file is the ``<service>`` tag, which may contain
``consts``, ``enums``, ``typedefs``, ``records``, ``exceptions``, ``classes``, 
and ``functions`` -- each of these element may in turn contain other 
sub-elements too.

.. _idl-doc:

A Note on Documentation
-----------------------
Every IDL element may include documentation, either as an attribute 
(``doc="foo bar"``) of the element itself, or as a sub-element called ``<doc>``.
For instance:

.. code-block:: xml
  
  <func name="foo" type="void">
      <doc>this is a documentation element, providing description 
      for the function foo. note that this text may span across several
      lines. you may use ReST formatting within comments, to add formatting
      to your documentation.</doc>
      <arg name="bar" type="int" doc="here's a short description of the argument 'bar'" />
      <arg name="spam" type="float">
          <doc>and this is equivalent to the ``doc`` element</doc>
      </arg>
  </func>

.. _idl-ids:

Unique IDs and Versioning
-------------------------
Every IDL element may specify its unique ID (an integer), as the attribute ``id``. 
These ID numbers are used to identify **functions, methods, and attributes** 
(properties) in the protocol level, and are thus important to multi-versioning 
(meaning, multiple versions of the IDL that need to work side-by-side). 
If an ID is omitted, a sequential auto-generated one is used -- but this means 
the order of the elements in the file matters (element A will receive a lower ID 
than element B if it precedes element B).

If both the client and the server are generated from the same IDL file, then 
there's no need to maintain the IDs of elements. However, if older versions of the
client have to work with a newer version of the server (or vice versa), then 
correct provisioning of IDs is crucial. The ID is used to invoke the correct
function, and if the ID of an element changes, older clients (using the old ID)
will attempt to invoke a wrong (possibly nonexistent) function. It is thus
important that elements that remain compatible between versions retain their
original ID number.

If a function prototype or semantics are changed, however, it is desired 
to assign it with a new ID number, so older clients won't accidentally attempt 
to invoke it, resulting in unexpected behavior: it is better to receive a
``ProtocolException`` saying the ID no longer exists than causing expected 
behavior.

Here's an example of how it's done:

.. code-block:: xml
  
  <func name="foo" type="void" id="3900">
      <arg name="bar" type="int"/>
  </func>


.. _idl-naming:

Naming Conventions
------------------
Since Agnos is used to bridge across different languages, each with its own
naming convention, it is desired to stick to a single naming convention for 
uniformity.

If you only use Agnos to interact within the same language, then you can use 
your target language's conventions. Otherwise, please use the following ones:

* Classes, Records, Exceptions and Enums (user-defined types): Camel-case, 
  starting with a capital letter (``HelloWorld``).
* Functions and Methods: Camel-case, starting with a lower-cased letter
  (``myFunction``).
* Constants and Enum-members: All capitals, words separated by underscores 
  (``MY_BITMASK``).
* Attributes (records and classes): All lower-case, words separated by 
  underscores (``my_attribute``).
* Typedefs: the rule is to use the same scheme of the original type. If the 
  original type is a built-in type, use an all lower-case name (like other 
  built-in types) -- ``<typedef name="real" type="float"/>``. 
  Otherwise, use camel-case starting with a capital letter -- 
  ``<typedef name="Hound" type="Dog"/>``.

.. _idl-annotations:

Annotations
-----------
Every IDL element can contain multiple sub-elements named ``annotation``, each
taking with two attributes: ``name`` and ``value``. This information is 
practically meaningless to the compiler, but allows you to add additional 
meta-information to the service, that could be used by other utilities or 
at runtime (through reflection :ref:`reflection <client-getServiceInfo>`).

For instance, you may want to mark certain functions as "more privileged" than
others, or limit them only to certain users. You could add this metadata as
an annotation on the function, for example,

.. code-block:: xml
  
  <func name="foo" type="void">
      <annotation name="user" value="johns">
      <arg name="bar" type="int"/>
  </func>

Again, this information is meaningless to the Agnos compiler, but it may be 
used by your implementation to deny access to any users other than ``johns``,
for instance.


------------------------------------------------------------------------------

.. _idl-service:

``service``
===========
The ``service`` element is the root element of every IDL specification; it 
provides the name of the service as well as some other optional information.

Syntax
------

``<service name="NAME" [versions="VERSIONS"] [package="PACKAGE"] [clientversion="CLIENT_VERSION"]>``

Contained Elements
------------------
* :ref:`idl-const`
* :ref:`idl-enum`
* :ref:`idl-typedef`
* :ref:`idl-record`
* :ref:`idl-exception`
* :ref:`idl-class`
* :ref:`idl-func`

Attributes
----------

``name``
^^^^^^^^
Required.

The name of the service. For example: ``name="toaster"``.
 
``package``
^^^^^^^^^^^
Optional.

The name of the package in the generated code. By default it's the name of the 
service, but you may want to change it. 
For example: ``package="com.foo.bar.toaster"``

.. _idl-service-versions:

``versions``
^^^^^^^^^^^^
Optional.

A comma-separated list of versions that this service is compatible with.
For example, suppose the first version of ``toaster`` was ``1.3``, and
in version ``1.4`` you added two functions. If version ``1.4`` is considered
compatible with ``1.3``, you should state so by writing ``versions="1.3,1.4"``.
If it is not compatible, and is meant to replace version ``1.3``, you should
write ``versions="1.4"``.

.. note::
  Versions names do not have to follow any format -- they are free-form text.
  However, it's expected you stick with the normal versioning conventions.

The order in which versions are specified is important; the oldest compatible
version should come first, and the latest compatible version should come last.
This is because the last version specified is considered to be the service's
version. For instance, in the case of ``versions="1.3,1.4"``, version ``1.4``
is considered to be the version of the service.

The main purpose of this feature is to allow clients of various versions to
connect to a single server. The server, naturally, has a single version -- 
but it may be compatible with multiple ones. This allows older clients to
connect to the service.

Version-compatibility is enforced when the client calls 
``assertServiceCompatibility`` (see :doc:`client`). 

``client_version``
^^^^^^^^^^^^^^^^^^
Optional.

The version that the client reports. By default, it's the service's version, 
meaning, the last version specified in the ``versions`` attribute.

.. note::
  For proper functioning, ``client_version`` must be listed as one of the 
  service' ``versions``.

------------------------------------------------------------------------------

.. _idl-const:

``const``
=========
Defines a constant value.

Syntax
------
``<const name="NAME" type="TYPE" value="VALUE" [namespace="NAMESPACE"] />``

Attributes
----------

``name``
^^^^^^^^
Required.

The name of the constant. For example: ``name="pi"``.

``type``
^^^^^^^^
Required.

The type of the constant. For example: ``name="float"``.

.. note::
  Constants may be of the following types: ``bool``, ``int8``, ``int16``, 
  ``int32``, ``int64``, ``float``, and ``string``. All other types are not
  currently supported.

``value``
^^^^^^^^^
Required.

The value of the constant. For example: ``name="3.1415926535"``. The format
of the value is like that of literals in most programming languages:
 
* Booleans are either ``true`` or ``false``
* Integral values are simply written out in base 10. Prefix the number by ``0x`` 
  for hexadecimal, ``0o`` for octal, and ``0b`` for binary.
* Floating point numbers follow the usual convention of ``[+-] DIGITS [.DIGITS] [E[+-]DIGITS]``
* Strings are written as is they are in most programming languages: surrounded by
  single quotes (``'``) or double quotes (``"``) and may contain the following 
  common escape-sequences: ``\n``, ``\t``, ``\r``, ``\\``, ``\"``, ``\'``, 
  and ``\xXX`` where ``XX`` consists of two hexadecimal digits.

``namespace``
^^^^^^^^^^^^^
Optional.

The namespace under which the constant "lives". This allows you to define two
constants with the same name that are contained in different namespaces. The
namespace plus the constant's name form the constant's *fully qualified name*.

The format is ``NAME1[.NAME2[.NAME3[...]]]``, meaning, a sequence of 
identifiers separated by periods. If no namespace is provided, the constant 
is placed in the "root" namespace. 

For example: 

.. code-block:: xml

  <const name="RED" type="int" value="7" />
  <const name="RED" type="int" value="3" namespace="foo.bar" />
  <const name="RED" type="int" value="6" namespace="spam.eggs" />

This will yield the constants ``RED``, ``foo.bar.RED``, and ``spam.eggs.RED``.

------------------------------------------------------------------------------

.. _idl-enum:

``enum``
========
Defines an enumeration, much like in ``C``.

Syntax
------
``<enum name="NAME" >``

Attributes
----------

``name``
^^^^^^^^
Required.

The name of the enum. For example: ``name="FileSystems"``.

Contained Elements
------------------
* :ref:`idl-member`

------------------------------------------------------------------------------

.. _idl-member:

``member``
==========
Defines an enumeration member. May only be placed within an ``enum``.

Syntax
------
``<member name="NAME" [value="VALUE"] >``

Attributes
----------

``name``
^^^^^^^^
Required.

The name of the enum member. For example: ``name="NTFS"``.

``value``
^^^^^^^^^
Optional.

The value of the enum member. If not given, the value is successor of the
previous value. The first value, if not given, is zero. 
For example: ``value="17"``.

------------------------------------------------------------------------------

.. _idl-typedef:

``typedef``
===========
Defines an alias for a type. Note that you may define a typedef of a type
before you've even defined it.

Syntax
------
``<typedef name="NAME" type="TYPE" >``

Attributes
----------

``name``
^^^^^^^^
Required.

The alias or the name of the "new type". For example ``name="real"``

``type``
^^^^^^^^
Required.

The actual type, to which you define the alias. For example ``type="float"``.


------------------------------------------------------------------------------

.. _idl-record:

``record``
==========
Defines a record of fields. Records, unlike :ref:`classes <idl-class>`, pass **by-value**.

Syntax
------
``<record name="NAME" [extends="NAME1,NAME2,..."] >``

Contained Elements
------------------
* :ref:`idl-record-attr`

Attributes
----------

``name``
^^^^^^^^
Required.

The name of the record. For example ``name="Point"``.

.. _idl-record-extends:

``extends``
^^^^^^^^^^^
Optional.

A comma-separated list of record names, which this record extends. Note that 
this is **different** from the notion of inheritance in object-oriented 
programming: when record A extends record B, it only means that A defines
all the fields that B defined, and perhaps more fields. 
This is mostly used as a syntactic sugar, but is more meaningful in the context 
of :ref:`exceptions <idl-exception>`. For instance, the following IDL

.. code-block:: xml

  <record name="Point2D">
      <attr name="X" type="float">
      <attr name="Y" type="float">
  </record>
  
  <record name="Point3D" extends="Point2D">
      <attr name="Z" type="float">
  </record> 

is equivalent to

.. code-block:: xml

  <record name="Point2D">
      <attr name="X" type="float">
      <attr name="Y" type="float">
  </record>
  
  <record name="Point3D">
      <attr name="X" type="float">
      <attr name="Y" type="float">
      <attr name="Z" type="float">
  </record> 

------------------------------------------------------------------------------

.. _idl-record-attr:

``attr``
========
Defines an attribute (also known as "field") within a record. 

Syntax
------
``<attr name="NAME" type="TYPE" />``

Attributes
----------

``name``
^^^^^^^^
Required.

The name of the attribute (field). For example ``name="age"``.

``type``
^^^^^^^^
Required.

The type of the attribute (field). For example ``type="int"``.

------------------------------------------------------------------------------

.. _idl-exception:

``exception``
=============
Defines an exception record. An exception is basically the same as a :ref:`idl-record`,
only it inherits the appropriate exception base-class of the target language.
Exception, being records, are passed **by-value**.

.. note::
  Unlike records, exceptions can extend only a single type, which must be an 
  exception on its own.

Syntax
------
``<exception name="NAME" [extends="NAME"] >``

Contained Elements
------------------
* :ref:`idl-record-attr`

Attributes
----------

``name``
^^^^^^^^
Required.

The name of the exception record. For example ``name="SomeError"``.

``extends``
^^^^^^^^^^^
Optional.

In addition to the :ref:`explanation above <idl-record-extends>`, it also 
generates the expected class-hierarchy. For instance, the following code

.. code-block:: xml
  
  <exception name="FooError">
      <attr name="message" type="str" />
  </exception>

  <exception name="BarError" extends="FooError">
      <attr name="error_code" type="int" />
  </exception>

will generate the exception classes ``FooError`` and ``BarError``, such that
``BarError`` derives from ``FooError``. This allows for catch-statements to work
as expected. 

------------------------------------------------------------------------------

.. _idl-class:

``class``
=========
Defines a class, containing attributes and methods. Instances of classes, 
in contrast to instances of :ref:`records <idl-record>`, pass **by-referernce**.

Syntax
------
``<class name="NAME" [extends="NAME1,NAME2,..."] >``

Contained Elements
------------------
* :ref:`idl-class-attr`
* :ref:`idl-class-method`
* :ref:`idl-class-inherited-attr`
* :ref:`idl-class-inherited-method`

Attributes
----------

``name``
^^^^^^^^
Required.

The name of the class. For example ``name="Person"``.

``extends``
^^^^^^^^^^^
Optional.

A comma-separated list of class names, which this class extends, in the normal
sense of inheritance in object-oriented programming, allowing for polymorphism.
Note that Agnos supports multiple-inheritance (as long as there is no 
name-collision), since in the implementation, classes are actually interfaces.

For example:

.. code-block:: xml
  
  <class name="Animal">
      <attr name="name" type="string"/>
      <method name="eat" type="void" />
  </class>

  <class name="Fish" extends="Animal">
      <method name="swim" type="void">
          <arg name="distance" type="int"/>
      </method>
  </class>

  <class name="Person" extends="Animal">
      <method name="walk" type="void">
          <arg name="distance" type="int"/>
      </method>
  </class>
  
  <func name="get_all_living_creatures" type="list[Animal]" />

The function ``get_all_living_creatures`` returns a list of ``Animals``, which
may be any of ``Animal``, ``Fish`` or ``Person`` (all up-casted to ``Animal``).
You can use down-casting to get the concrete type.

------------------------------------------------------------------------------

.. _idl-class-attr:

``attr``
========
Defines an attribute (also known as "property") within a class. 

Syntax
------
``<attr name="NAME" type="TYPE" [get="YESNO"] [set="YESNO"] [getid="INT"] [setid="INT"] />``

.. note::
  Class attributes are the only elements that do not accept an 
  :ref:`id attribute <idl-ids>`. Instead, they accept ``getid`` and ``setid``.

Attributes
----------

``name``
^^^^^^^^
Required.

The name of the attribute (property). For example ``name="account_number"``.

``type``
^^^^^^^^
Required.

The type of the attribute (property). For example ``type="int64"``.

``get``
^^^^^^^
Optional.

A boolean value (``yes/no`` or ``true/false``) indicating whether the attribute
supports read-access ("getting"). The default is "yes".

``set``
^^^^^^^
Optional.

A boolean value (``yes/no`` or ``true/false``) indicating whether the attribute
supports write-access ("setting"). The default is "yes".

``getid``
^^^^^^^^^
Optional.

The ID of the getter method (an integer). The default is an auto-generated one.
For example ``getid="3811"``.

``set``
^^^^^^^
Optional.

The ID of the getter method (an integer). The default is an auto-generated one.
For example ``setid="3812"``.

------------------------------------------------------------------------------

.. _idl-class-method:

``method``
==========
Defines a method of a class. Methods are essentially the same as 
:ref:`functions <idl-func>`, only they take an implicit argument, specifying the
object-id on which the operation is performed. 

Syntax
------
``<method name="NAME" type="TYPE" [clientside="YESNO"]>``

Contained Elements
------------------
* :ref:`idl-func-arg`

Attributes
----------

``name``
^^^^^^^^
Required.

The name of the method. For example ``name="bark"``.

``type``
^^^^^^^^
Required.

The return type of the method, which may be ``void`` if the method does not
return anything. For example ``name="string"``.

``clientside``
^^^^^^^^^^^^^^
Optional.

A boolean (``yes/no`` or ``true/false``) value indicating whether or not this 
method should be exposed in the generated client. Sometimes a method is 
deprecated in a later version of the service, but it is desired to keep it 
available for older clients. Setting this attribute to "no" will cause the 
relevant code to be generated only on the server-side, but not on the client.
This means up-to-date clients will not see it, but older ones will be able to
invoke it. The default is "yes".

------------------------------------------------------------------------------

.. _idl-class-inherited-attr:

``inherited-attr``
==================
A "phantom element", used only to specify the ``getid`` and ``setid`` of an
inherited :ref:`attribute <idl-class-attr>`. When your class needs to override
an inherited attribute and multi-versioning is required, you should use this
element to specify the new ``getid`` or ``setid`` of the overridden attribute.

Syntax
------
``<inherited-attr name="NAME" [getid="INT"] [setid="INT"] />``

Attributes
----------

``name``
^^^^^^^^
Required.

The name of the overridden attribute. Note that it must exist in one of the 
base-classes of this class, and that you cannot change its type.

``getid``
^^^^^^^^^
Optional.

The new ID of the getter function.

``setid``
^^^^^^^^^
Optional.

The new ID of the setter function.

------------------------------------------------------------------------------

.. _idl-class-inherited-method:

``inherited-method``
====================
A "phantom element", used only to specify the ``id`` of an inherited 
:ref:`method <idl-class-method>`. When your class needs to override an inherited 
method and multi-versioning is required, you should use this element to specify 
the new ``id`` of the overridden attribute.

Syntax
------
``<inherited-method name="NAME" id="INT" />``

Attributes
----------

``name``
^^^^^^^^
Required.

The name of the overridden method. Note that it must exist in one of the 
base-classes of this class, and that you cannot change its type or its arguments.

``id``
^^^^^^^^^
Required.

The new ID of the method.

------------------------------------------------------------------------------

.. _idl-func:

``func``
========
A function exposed by the service (also known as "static method").

.. note::
  ``function`` is an alias to ``func``

Syntax
------
``<func name="NAME" type="TYPE" [clientside="YESNO"] [namespace="NAMESPACE"]>``

Contained Elements
------------------
* :ref:`idl-func-arg`

Attributes
----------

``name``
^^^^^^^^
Required.

The name of the function. For example ``name="get_people"``.

``type``
^^^^^^^^
Required.

The return type of the function, which may be ``void`` if the function does not
return anything. For example ``name="list[Person]"``.

``clientside``
^^^^^^^^^^^^^^
Optional.

A boolean (``yes/no`` or ``true/false``) value indicating whether or not this 
function should be exposed in the generated client. Sometimes a function is 
deprecated in a later version of the service, but it is desired to keep it 
available for older clients. Setting this attribute to "no" will cause the 
relevant code to be generated only on the server-side, but not on the client.
This means up-to-date clients will not see it, but older ones will be able to
invoke it. The default is "yes".

``namespace``
^^^^^^^^^^^^^
Optional.

The namespace under which the function "lives". This allows you to define two
functions with the same name that are contained in different namespaces. The
namespace plus the functions's name form the function's *fully qualified name*.

The format is ``NAME1[.NAME2[.NAME3[...]]]``, meaning, a sequence of 
identifiers separated by periods. If no namespace is provided, the element
is placed in the "root" namespace. 

For example: 

.. code-block:: xml

  <func name="bark" type="void" />
  <func name="bark" type="void" namespace="foo.bar" />
  <func name="bark" type="void" namespace="spam.eggs" />

This will yield the functions ``bark``, ``foo.bar.bark``, and ``spam.eggs.bark``.

------------------------------------------------------------------------------

.. _idl-func-arg:

``arg``
=======
An argument of a :ref:`idl-func` or a :ref:`idl-class-method`.

Syntax
------
``<arg name="NAME" type="TYPE">``

Attributes
----------

``name``
^^^^^^^^
Required.

The name of the argument. For example ``name="age"``.

``type``
^^^^^^^^
Required.

The type of the argument. For example ``name="int"``.

------------------------------------------------------------------------------

.. _idl-example:

Example
=======
The following example demonstrates the use of all IDL elements:

.. code-block:: xml

  <service name="toaster" versions="1.3, 1.4">
      
      <typedef type="float" name="real" />
      
      <const name="pi" type="real" value="3.1415926535" />
      
      <enum name="BreadType">
          <member name="White" />
          <member name="Whole" />
      </enum>
      
      <enum name="Ingredient">
          <member name="Cheese" />
          <member name="Ham" />
          <member name="Olives" />
          <member name="Tomato" />
      </enum>
      
      <record name="Toast">
          <attr name="bread" type="BreadType" />
          <attr name="ingredients" type="list[Ingredient]" />
          <attr name="dressing" type="string" />
      </record>
      
      <exception name="MissingIngredient">
          <doc>sorry, but we're freshly out of some ingredient</doc>
          
          <attr name="ingredient" type="Ingredient" />
      </exception>
      
      <class name="Toaster">
          <method name="makeToast" type="Toast">
          </method>
      </class>
      
      <enum name="ToasterSize">
          <member name="Small" />
          <member name="Big" />
      </enum>
      
      <func name="get_toaster" type="Toaster" >
          <arg name="size" type="ToasterSize" />
      </func>
      
  </service>




