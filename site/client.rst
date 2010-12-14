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
endpoint. 

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
:doc:`over-http`.

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

.. note::
  The server process will terminate when the client closes the connection.

Aliases:

* ``C#``: ``Client.ConnectProc``
* ``C++``: ``SubprocClient`` class. Requires that ``BOOST_PROCESS_SUPPORTED`` 
  be defined.
* ``java``: ``Client.connectProc``
* ``python``: ``Client.connect_executable`` or ``connect_proc``






.. _client-methods:

Client Methods
==============

``assertServiceCompatibility``
------------------------------
Asserts that the server is compatible with this version of the client. The 
function does not return a value; instead it throws an exception if the client
is incompatible with the server, or returns silently if everything is well.

Although not mandatory, you **should** call this method right after 
establishing a connection, to make sure your client is compatible with the 
server. Otherwise, you may be working with an incompatible server, 
which may lead to unexpected behavior!

.. note::
  In future versions, ``assertServiceCompatibility`` may automatically be
  called when establishing a connection.

``close``
---------
Closes the underlying transport and terminates the connection. This function
will be implicitly called by ``Dispose`` or the destructor of the connection.


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
* ``INFO_FUNCCODES`` (3) - returns a map of functions names to their unique IDs
* ``INFO_REFLECTION`` (4) - returns information about all the types defined by
  the service. This includes records, enums, and classes, as well as 
  service-level information, which includes functions and constants. The 
  returned information allows you to virtually construct the IDL from which 
  service was generated.

Any other value for ``code`` will return the same result as ``INFO_META``,
and is reserved for future use.


.. _client-proxies:

Proxies
=======

How Proxies Work
----------------
TDB

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

castToXXX (check = true/false) -> XXX
getProxyType() -> string










