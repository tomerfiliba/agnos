.. _doc-srcgen:

``srcgen``
==========
The *Source Generator*, most commonly known as ``srcgen`` (pronounced "source gen"),
is a :ref`command-line utility <tool-agnosrc-py>`, distinct from the 
:ref:`Agnos compiler <tool-agnosc>`, that processes special comments placed 
inside source code, and automatically generates the necessary 
:ref:`Agnos IDL<doc-idl>`. Currently the utility only supports processing ``python`` 
packages, but future versions will include ``srcgen`` for ``C#`` and ``java`` 
(see `planned features <http://github.com/tomerfiliba/agnos/issues/labels/planned%20features>`_). 

Purpose
-------
The approach of maintaining an IDL file separately from the code base works 
well for smaller projects or services, as it allows for decoupling between the 
service and its implementation. However, in larger projects, where it's very
likely that the service and its implementation are tightly coupled anyway,
this approach is has numerous disadvantages:

* XML was not designed for humans. It may be easy to parse and process 
  programmatically, but it's unreadable, repetitive, and cumbersome. 
* Two places to edit: when making changes to the code, you have to remember
  to update the IDL accordingly. It's likely the two will go out of sync.
* The IDL becomes large and hard to maintain. It's likely a team of developers 
  would run into edit collisions, and it's hard to make your way around and 
  find what you were looking for.
* You have to manually write the binding between your code base and the
  Agnos-generated code, implement all interfaces, etc.

This is exactly the gap that ``srcgen`` comes to fill. Instead of writing an 
IDL and then implementing it in code -- ``srcgen`` goes the other way around. 
You start with an existing code base (or package) and add annotations, in the
form of special in-code comments, that provide the information required for
the Agnos compiler. Conceptually, the IDL and the implementation become one.
This means you no longer have to write XML, there's only a single place to edit,
and the "IDL" is logically divided into files, which makes collisions rare 
and finding what you need easy. 

On top of all that, ``srcgen`` also **automatically generates a server** that 
exposes your service. It essentially does the all the wiring for you. Isn't that
sweet?

.. note::
  As stated before, ``srcgen`` only supports ``python`` packages. Support for 
  other languages is planned.


Syntax
------
``srcgen`` processes special comments that are placed inside the code base. 
These comments start with the language's single-line comment marker (``#`` 
in ``python``), followed by two colons (``::``)), and then tokens. If the
first token begins with ``@``, the line is interpreted as a *tag*, otherwise
it's interpreted as documentation (free-form). The ``srcgen`` utility scans
a directory (recursively) and collects all the special comments from all the
source code files (for ``python``, ``*.py``).

The syntax of tags is the following:

``#:: @TAG {NAME|name=NAME} [ARG1=VAL1] [ARG2=VAL2] ...``

Because the ``name`` attribute appears in all tags, a syntactic-sugar has been
added for it: if the first token following the tag does not contain an *equals
sign* (``=``), it's used as the tag's name. Of course you may explicitly 
specify the tag's name, in which case you're not limited to place it as the
first token. For instance, ``@func bar type=eggs`` is identical to 
``@func type=eggs name=bar``.

..note:: 
   The order in which the attributes appear is not meaningful. You may change 
   it freely.

There are three kinds of attributes:

* *Mandatory* -- attributes that must be explicitly assigned; ``srcgen`` will 
  fail with an error message if they are omitted.

* *Inferred* -- required attributes that may be omitted, in which case ``srcgen``
  will attempt to infer their value from the source code. For example, the
  ``name`` argument of ``@func`` may be either assigned of omitted (and then 
  the name of the function in the code (``def foo(...):``) will be used.
  See more at :ref:`tags <srcgen-tags>`

* *Optional* -- attributes that may be omitted; usually those have a default
  value.


Structuring by Indentation
^^^^^^^^^^^^^^^^^^^^^^^^^^
Tags can be nested within one another. For example, a ``@class`` tag could
contain nested ``@method`` tags, and each one of them may contain nested 
``@arg`` tags. This is achieved by the use of **indentation**, must like in 
normal ``python`` code: if tag ``A`` is placed deeper than tag ``B`` (within 
the same file), ``A`` will be a child of ``B``. For instance::

  #:: @class Turle
  class Turle(object):
      #:: @method walk type=void
      #::     @arg distance type=int
      #::     @arg angle type=int
      def walk(self, distance, angle):
          pass

This eases the cumbersomeness of XML documents, reducing visual noise and 
clutter.

Both the whitespace before and after the comment marker matters -- so this 
code snippet is identical to the previous one::

  #:: @class Turle
  class Turle(object):
      #:: @method walk type=void
          #:: @arg distance type=int
  #::         @arg angle type=int
      def walk(self, distance, angle):
          pass

Of course it's more sensible to place the marker at the same indentation level 
as the code it describes, to increase readability. 

.. note::
  As a word of advise, use **spaces to indent the elements, rather than 
  tabs**, and avoid completely mixing the two, or it would be a nightmare to
  debug. This also adheres to the ``python`` convention. 


Documentation and Docstrings
^^^^^^^^^^^^^^^^^^^^^^^^^^^^
As said before, special comments may be either tags (if the begin with the ``@``
symbol) or free-form comments (if they do not start with ``@``). This means you
can attach documentation to the to tag. For example::

  #:: @func answer type=int
  #::    this function returns a very special number, one which can be 
  #::    used as the answer to life, the universe and everything.
  #::
  #::    @arg a type=int
  #::        your guess of what the answer is
  def answer(a):
      return a + 42 - a

.. note::
  Indentation matters! Comments that belong to a tag must be more deeply-indented 
  than the tag. Also, comments and child-tags must be indented to the same level:
  if the ``@arg`` tags is 4 spaces deeper than the ``@func`` tag, so should all
  comment lines be 4 spaces

If no documentation is provided as a nested special-comment, ``srcgen`` will
attempt to look for `docstrings <http://en.wikipedia.org/wiki/Docstring>`_ 
following the tag, and use them. For instance, the following code should produce
the same results as the snippet above::

  #:: @func answer type=int
  #::    @arg a type=int
  #::        your guess of what the answer is
  def answer(a):
      """this function returns a very special number, one which can be 
      used as the answer to life, the universe and everything."""
      return a + 42 - a


Layout 
^^^^^^
Tags are normally placed **right above** the source code they describe. This is 
not a general requirement, as ``srcgen`` simply collects all the special 
comments and there's no way to guarantee any particular order for that.
However, following this convention has two benefits: it increases the 
**readability and maintainability** of the IDL and source code, since it's
easy to see the whole picture together and update a single place in the code,
and it allows for **attributes to be inferred**. 

If you wish to use *inferred attributes*, you must place the tags directly
above the code they describes. It allows ``srcgen`` to locate the code block
that follows and parse it. For instance, if you write ::


  #:: @func type=int
  def foo():
      return 5

``srcgen`` will automatically infer the ``name`` attribute to be ``foo``. If 
you place the special comment right above the code block, you must specify
the name explicitly -- or ``srcgen`` might infer a wrong name (or fail 
completely).


Whitespace
^^^^^^^^^^
Whitespace is used as the **token delimiter** in tags. This means that you 
cannot use whitespace in either names or values of attributes. Later versions 
of ``srcgen`` may add quoting or escaping support, but this is not currently 
implemented. Although this may first strike you as a limitation, it's hardly
so. There is virtually no need for names or attributes to contain whitespace,
as they are almost exclusively used as programmatic identifiers. 

You should always use alpha-numeric identifiers (underscores allowed). For 
instance, these are all **wrong** (and will cause parsing errors):
* ``@func name=lady gaga``
* ``@func name="lady gaga"``
* ``@func lala=lady\ gaga``

Do note that the equals sign may be separated from its arguments by whitespace.
For instance, ``@func name=foo`` and ``@func name = foo`` are identical.

As previously states, attribute names or values represent identifiers (such as 
type names), and there's little chance you'd get them wrong. There are two 
cases, however, where it's of the essence:

* **Comma-separated lists** of values (e.g.,``@service Foobar versions=1,2,3,4`` or
  ``@class extends=Spam,Bacon``). Comma-separated values must not be separated 
  by spaces (e.g., ``@service Foobar versions=1, 2, 3, 4`` is **wrong**)

* **Constant values** (e.g., ``@const PI type=list[int] value=[3,4,5]``).
  Do not use whitespace between tokens (e.g., 
  ``@const PI type=list[ int ] value=[3, 4, 5]`` is **wrong**). Also, if you 
  need to define string constants that contain spaces, use **string escaping**
  (e.g. ``@const MESSAGE type=str value=hello\x20world``). Note that may times
  a constant's value may be inferred directly from the source code, in which 
  case these restrictions do not apply.


Example
-------
Enough talk -- here's a code example::

  #:: @service MinistryOfInterior
  
  #:: @module foo.bar 
  
  #:: @class
  class Person(object):
      #:: @attr full_name type=str access=get
      #:: @attr date_of_birth type=date access=get
      #:: @attr spouse type=Person access=get
  
      def __init__(self, name):
          self.full_name = name
          self.date_of_birth = datetime.now()
          self.spouse = None
      
      #:: @method type=void
      #::     Marries `self` with `other`. Note that `self` and `other` must
      #::     not be already married.
      #::
      #::     @arg other type=Person
      #::         The person `self` is to marry
      def marry(self, other):
          assert self.spouse is None, "already has a spouse"
          assert spouse.spouse is None, "spouse already has a spouse"
          self.spouse = spouse


.. _srcgen-tags:

Tags
----
The tags essentially reflect the IDL elements, so when in doubt consult the
doc:`IDL reference<idl>`. However, not all tags appear in the IDL, as some 
expose more "advanced" concepts, which are converted to the building blocks of
the IDL. For instance, the ``@staticmethod`` tag is actually converted to 
a ``func`` element in the IDL, with the namespace being the class' name.


.. _srcgen-service:

``@service``
^^^^^^^^^^^^
**Format**: ``@service NAME [package=PACKAGE] [versions=VERSIONS] [clientversion=CLIENTVERSION]`` 

**IDL element**: :ref:`idl-service`

**Nested tags**: N/A

The ``@service`` tag **must appear exactly once** throughout the package 
(source code tree). It specifies the service' name and some other optional 
attributes. It would be wise to place this tag in the root of the package, 
say the topmost ``__init__.py`` file.

Note: ``VERSIONS`` is comma-separated list of versions. For instance, 
``versions=1.0,1.1,1.2``.


.. _srcgen-module:

``@module``
^^^^^^^^^^^
**Format**: ``@module NAME [namespace=NAMESPACE]`` 

**IDL element**: N/A

**Nested tags**: N/A

May appear once per module. It specifies the module's full name, i.e.,
the name that may be used to import that module from outside the package,
and optionally, the default namespace under which the functions and 
constants of this module would be exposed.

If the ``@module`` tag does not appear, ``srcgen`` uses the relative path of 
that module from the package's root. However, although optional, it is 
advisable that you place this tag in all of the modules you wish to expose.


.. _srcgen-annotation:

``@annotation``
^^^^^^^^^^^^^^^
**Format**: ``@annotation NAME value=VALUE``

**IDL element**: :ref:`idl-annotations`

**Nested tags**: N/A

Adds an annotation to the element that contains it. All tags can have nested 
annotations, but they are most commonly used in ``@func`` and ``@method`` tags.

Example::

  #:: @func type=int
  #::     @annotation user value=johns
  def foo():
      pass

.. _srcgen-const:

``@const``
^^^^^^^^^^
**Format**: ``@const NAME type=TYPE value=VALUE``

**IDL element**: :ref:`idl-const`

**Nested tags**: N/A

Defines a constant. The ``NAME`` and ``VALUE`` attributes can be inferred (to 
some extent). For example::

  #:: @const type=float
  PI = 3.1415926535


.. _srcgen-enum:

``@enum``
^^^^^^^^^
**Format**: ``@enum NAME``

**IDL element**: :ref:`idl-enum`

**Nested tags**: :ref:`srcgen-member`

Defines an enum. The ``NAME`` attribute can be inferred. You can use this tag in
two ways, the first being ::

  #:: @enum FileSystem
  #::     @member NTFS
  #::     @member FAT16 value=3
  #::     @member FAT32 value=8
  #::     @member EXT2

Or more commonly ::

  #:: @enum
  class FileSystem(object):
      #:: @member
      NTFS = 0
      #:: @member
      FAT16 = 3
      #:: @member
      FAT32 = 8
      #:: @member
      EXT2 = 9


.. _srcgen-member:

``@member``
^^^^^^^^^^^
**Format**: ``@member NAME [value=VALUE]``

**IDL element**: :ref:`idl-member`

**Nested tags**: N/A

Defines an enum member. The ``NAME`` and ``VALUE`` attributes can be inferred.
See example above.


.. _srcgen-record:

``@record``
^^^^^^^^^^^
**Format**: ``@record NAME [extends=EXTENDSLIST]``

**IDL element**: :ref:`idl-record`

**Nested tags**: :ref:`srcgen-record-attr`

Defines a record. The ``NAME`` and ``EXTENDSLIST`` attributes can be inferred 
(see more about :ref:`inferred inheritance <srcgen-inheritance>`). For example::

  #:: @record
  class Address(object):
      #:: @attr country type=str
      #:: @attr city type=str
      #:: @attr street type=str
      #:: @attr num type=int
      
      def __init__(self, country, city, street, num):
          self.country = country
          self.city = city
          self.street = street
          self.num = num


.. _srcgen-record-attr:

``@attr``
^^^^^^^^^
**Format**: ``@attr NAME type=TYPE``

**IDL element**: :ref:`idl-record-attr`

**Nested tags**: N/A

Defines a record attribute. All attributes are mandatory and none can be 
inferred. See example above.

.. _srcgen-exception:

``@exception``
^^^^^^^^^^^^^^
**Format**: ``@exception NAME [extends=NAME]``

**IDL element**: :ref:`idl-exception`

**Nested tags**: :ref:`srcgen-record-attr`

Defines an exception record. This is essentially the same as a
:ref:`srcgen-record`, only it derives from the target language's base 
exception class. The ``NAME`` and ``EXTENDS`` attributes can be inferred.
Note that unlike records, exceptions may extend only a single type, which must
be an exception by itself. For example::

  #:: @exception
  class CLIError(Exception):
      #:: @attr command type=str
      #:: @attr parameters type=list[str]
      
      def __init__(self, command, params):
          self.command = command
          self.parameters = params

  #:: @exception
  class CLIExecutionFailed(CLIError):
      #:: @attr errorCode type=str
      
      def __init__(self, command, params, errorCode):
          CLIError.__init__(self, command, params)
          self.errorCode = errorCode


.. _srcgen-class:

``@class``
^^^^^^^^^^
**Format**: ``@class NAME [extends=EXTENDSLIST]``

**IDL element**: :ref:`idl-class`

**Nested tags**: :ref:`srcgen-class-attr`, :ref:`srcgen-method`, 
:ref:`srcgen-staticmethod`, :ref:`srcgen-ctor`

The ``NAME`` and  and ``EXTENDSLIST`` can be inferred (see more
about :ref:`inferred inheritance <srcgen-inheritance>`). For example::

  #:: @class
  class Person(object):
      #:: @attr first_name type=str access=get
      #:: @attr last_name type=str access=get
      #:: @attr spouse type=Person access=get
      #:: @attr hobbies type=list[str] access=get,set
      
      def __init__(self, first_name, last_name):
          self.first_name = first_name
          self.last_name = last_name
          self.spouse = None
          self.hobbies = []
      
      #:: @method type=void
      #::     @arg other type=Person
      def marry(self, other):
          pass


.. _srcgen-class-attr:

``@attr``
^^^^^^^^^
**Format**: ``@attr NAME type=TYPE [access=GETSET]``

**IDL element**: :ref:`idl-class-attr`

**Nested tags**: N/A

Defines a class attribute. ``GETSET`` can be ``get``, ``set``, or ``get,set`` --
the default is ``get,set`` (meaning read-write access). None of the attributes
can be inferred. See example :ref:`above <srcgen-class>`.


.. _srcgen-method:

``@method``
^^^^^^^^^^^
**Format**: ``@method NAME [type=TYPE] [version=VERSION]``

**IDL element**: :ref:`idl-class-method`

**Nested tags**: :ref:`srcgen-arg`

Defines a method, i.e., a function that's bound to an instance of the class.
The ``NAME`` attribute can be inferred. ``TYPE`` is ``void`` by default. 
``VERSION`` is undefined by default. See more
about :ref:`versioning <srcgen-versioning>`. See example 
:ref:`above <srcgen-class>`.

.. note::
  The ``self`` argument of every python method is not considerred an argument
  of the method, and should **not** be included as an ``@arg``.


.. _srcgen-staticmethod:

``@staticmethod``
^^^^^^^^^^^^^^^^^
**Format**: ``@staticmethod NAME [type=TYPE] [version=VERSION]``

**IDL element**: :ref:`idl-func`

**Nested tags**: :ref:`srcgen-arg`

Defines a static method, i.e., a method that is not bound to an instance of
the class. Static methods are basically normal functions that live in the 
class' namespace -- and in fact, that's how they are converted to the IDL.

``TYPE`` is ``void`` by default. ``VERSION`` is undefined by default. See more
about :ref:`versioning <srcgen-versioning>`.

Example ::

  #:: @class
  class File(object):

      def __init__(self, filename, mode):
          self._file = open(filename, mode)
      
      #:: @staticmethod type=File
      #::     @arg filename type=str
      @staticmethod
      def open_readonly(filename):
          return File(filename, "r")

      #:: @staticmethod type=File
      #::     @arg filename type=str
      @staticmethod
      def open_readwrite(filename):
          return File(filename, "r+")
      
      #:: @method type=buffer
      #::     @arg count type=int
      def read(self, count):
          return self._file.read(count)

Note that the static-method ``open_readonly``, for instance, is converted to
the following IDL:

.. code-block:: xml

  <func name="open_readonly" type="File" namespace="File"> ... </func>

and is later accessible through the ``File`` namespace, like so ::

  c = Client.connect("...")
  c.File.open_readonly("/tmp/foo.bar")


.. _srcgen-ctor:

``@ctor``
^^^^^^^^^
**Format**: ``@ctor [version=VERSION]``

**IDL element**: :ref:`idl-func`

**Nested tags**: :ref:`srcgen-arg`

Defines the constructor of a class. Only one such constructor may be defined.
The constructor is basically a :ref:`static method <srcgen-staticmethod>` that
is named ``ctor``, in the namespace of the class, may take any number of
arguments, and returns an instance of the class. 

``VERSION`` is undefined by default. See more about 
:ref:`versioning <srcgen-versioning>`.

Example ::

  #:: @class
  class File(object):
      
      #:: @ctor
      #::     @arg filename type=str
      #::     @arg mode type=str
      def __init__(self, filename, mode):
          self._file = open(filename, mode)
          
      #:: @method type=buffer
      #::     @arg count type=int
      def read(self, count):
          return self._file.read(count)

Note that the constructor need not always be the ``__init__`` method; any 
static-method (or ``@classmethod`` in ``python``) will do::

  #:: @class
  class File(object):
  
      def __init__(self, filename, mode):
          self._file = open(filename, mode)

      #:: @ctor
      #::     @arg filename type=str
      #::     @arg mode type=str
      @staticmethod
      def open(filename, mode):
          return File(filename, mode)
      
      #:: @method type=buffer
      #::     @arg count type=int
      def read(self, count):
          return self._file.read(count)



.. _srcgen-func:

``@func``
^^^^^^^^^
**Format**: ``@func NAME [type=TYPE] [version=VERSION]``

**IDL element**: :ref:`idl-func`

**Nested tags**: :ref:`srcgen-arg`

Defines a function. The ``NAME`` attribute can be inferred.
``TYPE`` is ``void`` by default. ``VERSION`` is undefined by default (see more
about :ref:`versioning <srcgen-versioning>`). For example::

  #:: @func type=int
  #::     @arg x type=int
  def squared(x):
      return x*x


.. _srcgen-arg:

``arg``
^^^^^^^
**Format**: ``@arg NAME type=TYPE``

**IDL element**: :ref:`idl-func-arg`

**Nested tags**: N/A

Defines a argument of a ``@function``, a ``@method``, a ``@staticmethod`` or 
a ``@ctor``. Both arguments are mandatory and cannot be inferred. See example
:ref:`above <srcgen-func>`.


--------------------------------------------------------------------------------

.. _srcgen-inheritance:

Inheritance
-----------
``srcgen`` is able to parse the inheritance list of classes and records, and
extract the ``EXTENDSLIST`` automatically: if the inheritance list contains a
name that has been exposed with ``srcgen``, it will be incorporated into
the ``EXTENDSLIST``. If the name has not been exposed, it will be ignored.
Consider the following code::

  #:: @class
  class A(object):
      pass
      
  class B(object):
      pass
      
  #:: @class
  class C(A, B):
      pass

Only ``A`` will be in the ``EXTENDSLIST`` of class ``C``, since ``B`` was not
exposed. 

The same applies to ``@record`` and ``@exception`` tags.


.. _srcgen-versioning:

Versioning 
----------
With time, there will certainly be changes in your project that are incompatible
with older versions. For instance, a function may be removed or its 
signature may change. This is acceptable as long as all the consumers of your
service are kept up-to-date in accordance with the changes -- but this is 
hardly ever possible. When the number of consumers of the service grows larger,
it become less and less plausible that they could all be updated to reflect 
every such change.

Taking this into account, ``srcgen`` allows you to define **multiple versions**
of functions, methods, static methods, and constructors. For instance, say
version 1 of your service exposed the following function::

  #:: @func type=int
  #::     @arg x type=int
  def squared(x):
      return x**2

and in version 2, you decided to change the type from ``int`` to ``float``::

  #:: @func type=float
  #::     @arg x type=float
  def squared(x):
      return x**2

This renders the two versions of your service incompatible. One solution would
be to update all your clients, but as said before, this is not always possible.
Luckily, ``srcgen`` allows you to have multiple versions of the same function,
methods, static-method or constructor -- that all live side-by-side. For 
instance, you'd want to have two versions of ``squared`` -- version 1 and 2.
Older clients, that expect to find version 1, would still use version 1, but
newer clients, that are aware of version 2, would use version 2. This can be 
achieved by the ``version`` attribute::

  #:: @func squared type=int version=1
  #::     @arg x type=int
  def squared1(x):
      return x**2

  #:: @func squared type=float version=2
  #::     @arg x type=float
  def squared2(x):
      return x**2

..note:: 
  The two functions were renamed, so that both could exist in the same module.
  If, for instance, the two existed in different modules, they could both be
  named ``squared``.  

Another thing you'd have to do is update the :ref:`versions <idl-service-versions>`
attribute of the ``@service`` tag::

  #:: @service MathStuff versions=1,2

This tells your clients that the service supports two co-exsting versions, 1 
and 2, and clients can check their compatibility with your server using the
:ref:`client-assertServiceCompatibility` method.

This solves the problem neatly, as older clients (that are not aware of 
version 2) can keep using version 1 of ``squared``, while newer clients will
its second version. 


The "history file"
--------------------
The "history file" is one of the files that's generated by ``srcgen`` in the
process. It is a very simple text file that maps IDs to fully-qualified names,
and allows ``srcgen`` to assign the same IDs to the same functions every time.
Without the history file, functions would be assigned arbitrary IDs, which
would render older clients incompatible, since they would use different IDs
than the server's. 

.. note::
  You should add the history file to your source control repository, as it's 
  quite valuable. Without it, every time ``srcgen`` processes your code, IDs
  may be assigned differently.
  
  Unless you update all of your clients every time the server is re-generated,
  the history file is important to you. 



