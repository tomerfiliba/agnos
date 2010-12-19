Client-Side APIs
================
This section describes all the client-side APIs required to write an Agnos 
client. 

Note that ``libagnos`` uses the naming conventions of each language, so the 
names slightly differ. Throughout the documentation, we use the ``java`` name 
as the "official" one, but the other names are listed too. In C++, since 
factory methods are not supported natively, ``libagnos`` makes use of classes 
instead.


.. _client-factory:

Creating a Client
=================
The ``Client`` class comes with several factory methods that ease the 
construction of ``Client`` instances. You will usually use one of these factories,
although you can construct a ``Client`` instance directly by instantiating it
with an ``ITransport`` instance.


``connectSock``
---------------
Creates an Agnos connection, over a socket. Parameters are ``hostname`` and 
``port_number``, or any of the language's standard ways to represent a TCP 
endpoint. An optional parameter, ``checked``, determines whether 
``assertServiceCompatibility`` is automatically called (``true`` by default).

Aliases:

* ``C#``: ``Client.ConnectSocket``
* ``C++``: ``SocketClient`` class
* ``java``: ``Client.connectSock``
* ``python``: ``Client.connect``

``connectUrl``
--------------
Creates an Agnos connection that operates on top of HTTP requests to the given
URL. In this mode, the payload (binary) will be wrapped with the proper
HTTP header, which allows it to integrate with an HTTP server. See also 
:doc:`over-http`. An optional parameter, ``checked``, determines whether 
``assertServiceCompatibility`` is automatically called (``true`` by default).

Aliases:

* ``C#``: ``Client.ConnectUri``
* ``C++``: ``UrlClient`` class. Not yet implemented.
* ``java``: ``Client.connectUrl``
* ``python``: ``Client.connect_url``

``connectProc``
---------------
Connects to a newly-spawned process server (see more under :doc:`library-mode`).
It takes the filename of the process to spawn, or a ``ProcessBuilder`` instance,
spawns the process and establishes an Agnos connection to it. 
An optional parameter, ``checked``, determines whether 
``assertServiceCompatibility`` is automatically called (``true`` by default).

.. note::
  In *library mode*, the server process will terminate when the client closes
  the connection.

Aliases:

* ``C#``: ``Client.ConnectProc``
* ``C++``: ``SubprocClient`` class. Requires that ``BOOST_PROCESS_SUPPORTED`` 
  be defined.
* ``java``: ``Client.connectProc``
* ``python``: ``Client.connect_executable`` or ``connect_proc``



.. _client-methods:

Client Methods
==============

.. _client-assertServiceCompatibility:

``assertServiceCompatibility``
------------------------------
Asserts that the server is compatible with this version of the client. The 
function does not return a value; instead it throws an exception if the client
is incompatible with the server, or returns silently if everything is well.

As a precaution, ``assertServiceCompatibility`` is automatically called when
a new connection is established. To disable this when using one of the 
``connectXXX()`` factory methods, set ``checked`` to ``false``. 
It is **advisable**, however, not to disable this check, or your client might 
be incompatible with the server, leading to unexpected behavior!

.. note::
  There is usually no need to call this method explicitly, unless you set
  ``checked`` to ``false`` when connecting. 


``close``
---------
Closes the underlying transport and terminates the connection. This function
will be implicitly called by ``Dispose`` or the destructor of the connection.


.. _client-getServiceInfo:

``getServiceInfo``
------------------
Returns a :ref:`type-heteromap` containing various information about the service. 
It takes ``code``, an integer specifying the requested information. Acceptable
values are:

* ``INFO_META`` (0) - returns "meta information" about the supported info codes
* ``INFO_GENERAL`` (1) - returns general information about the service, 
  including its name, versions, SHA1 of the IDL, etc. 
* ``INFO_FUNCTIONS`` (2) - returns information about the **low-level** functions
  exposed by this service, including their names, signatures, and unique 
  identifiers. Note that this provides a "flat" view of the service; methods
  and class attributes are shown in their true nature -- as functions that
  accept an implicit first argument that represents the object on which they
  operate.
* ``INFO_REFLECTION`` (3) - returns information about all the types defined by
  the service. This includes types like records, enums, and classes, as well 
  as service-level information, like functions and constants. The 
  returned information allows you to virtually construct the IDL from which 
  service was generated.

Any other value for ``code`` will return the same result as ``INFO_META``,
and is reserved for future use.


.. _client-proxies:

Proxies
=======
Unlike records, enums, and other simple types, instances of :ref:`classes <idl-class>`
pass by reference. This means the actual object remains on the server (AKA 
*remote object* or *referenced object*), and only a unique identifier
is sent to the client (AKA *object ID* or *object reference*). 

In order to make working with remote objects easy, a *proxy object* is created
on the client, which represents the remote one: a proxy class is generated for 
every class defined in the IDL (with the name name as the original class, 
suffixed by ``Proxy``). 

The purpose of the proxy instance is to hide the inner details of passing 
objects *by reference*. The proxy instance has the same "look and feel" of
the remote object -- exposing the same methods and attributes.


Casting
-------
Agnos supports polymorphism of proxies, meaning, a proxy instance can be
up-casted to one of it's super classes, or down-casted to one of it's
derived classes. This is done by the ``castToXXX`` family of methods that 
the proxy supports.

For example, suppose you have ``ClassA``, ``ClassB`` that derives 
from ``ClassA``, and a function ``foo``, whose return type is ``ClassA``.
When you invoke ``foo``, you receive an instance of type ``ClassAProxy``,
that exposes the same interface as ``ClassA``, as defined in the IDL.
However, the actual instance returned by ``foo`` may also be ``ClassB``, since
it's compatible with ``ClassA``. 

``discard``
^^^^^^^^^^^
Discards the proxy. This will inform the server to decrease the reference count
of the remote object. Once the refcount reaches 0, the remote object will be 
garbage-collected.

After calling this method, the proxy instance can no longer be used; this will
automatically be called when the proxy instance is garbage-collected, thus
you shouldn't normally have to call this function explicitly.

``castToXXX``
^^^^^^^^^^^^^
The proxy class can be up-casted or down-casted to any of the class' super classes
or derived classes. This is done with the ``castToXXX`` family of functions, where
``XXX`` is the super class' or derived class' name. 

In our example above, instances of ``ClassAProxy`` expose a ``castToClassB``
method, and instances of ``ClassBProxy`` expose a ``castToClassA``. Calling
``castToXXX`` returns a **new proxy object** that exposes the methods and
attributes of the desired type. As with all runtime casts, it might fail.

Each of the ``castToXXX`` functions takes an optional parameter, ``checked``,
which is ``false`` by default, meaning the cast may work locally, but when
you'd try to use the methods or attributes of the object, it might fail.
If you set ``checked`` to ``true``, the cast will be checked against the server,
making sure it's legal. If illegal, an exception will be raised. 

``getRemoteType``
^^^^^^^^^^^^^^^^^
This method is supported by all proxies, and returns the runtime-type of the 
referenced object on the server. The return value is a string, representing
the fully qualified type name.


