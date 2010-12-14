Library Mode
============

*Library Mode* allows you to spawn an Agnos server process and connect to it
directly, instead of having to set up a separate server, publish its TCP port,
and manage its life-cycle. The procedure that Agnos employs is very simple:
 
1. The client spawns the server process (possibly specifying ``-m lib`` for the 
   command-line arguments)
2. The server chooses a random port to listen on, and writes this port number 
   on to ``stdout``
3. The client reads the server's port from ``stdout`` and connects to it directly
4. Once the client closes the socket, the server process dies along with it

A Brief History
---------------
The *library mode* was a fundamental requirement from Agnos. When we started
Agnos, our first and foremost purpose was to allow clients (written in different 
languages) to utilize our libraries, and we wanted the process to be as smooth
as possible. This is why Agnos supports this seemingly trivial-to-implement
feature internally. 

Initially, we sought to implement *library mode* over pipes or Unix-domain 
sockets, for greater efficiency. However, being a cross-platform library meant
we had to resort to using this scheme (of regular TCP sockets) on some platforms,
and besides, it turned out that Unix-domain sockets are 
`not faster <http://comments.gmane.org/gmane.comp.lib.thrift.user/830>`_ 
than ``localhost`` -bound sockets, since the network stack has been heavily 
optimized for this case (both on Linux and Windows). So all in all, the marginal
performance gain was not worth the effort.

Usage
-----
To create a *library mode* connection, you can use the ``ConnectProc`` 
factory-method of the ``Client`` class. The function goes by different names
in different languages (see :ref:`more here <client-factory>`). It takes
the filename of the process to spawn, and optionally custom command-line 
arguments. 

Example:

.. code-block:: c#

  MyService.Client client = MyService.MyClient.ConnectProc(@"c:\path\to\myserver.exe");

In our products, we provide an ``Initialize`` factory method that locates the
server's path automatically. This way, all the end user has to do is:

.. code-block:: c#

  MyService.Client client = MyService.Initialize();







