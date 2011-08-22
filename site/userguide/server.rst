.. _doc-server:

Server-Side APIs
================

This section describes writing the server-side implementation of an Agnos 
service. As with the :ref:`doc-client`, the API names vary slightly between 
languages, since ``libagnos`` follows the naming convention of each language.
The "official" name is the ``java`` one, and the code snippets here are given
in ``java``, assuming it's popular enough to serve as *lingua franca*.


Writing a Server
----------------
There are two parts to implementing an Agnos service:

1. Implementing the ``IHandler`` interface, which contains all the functions 
   defined in the service.
2. Implementing all the classes defined in the service' IDL. This includes
   the classes methods and attributes. For every class in your IDL, an 
   interface named ``IClassName`` is defined, which you should implement.

.. code-block:: java

  import my.service.package.server_bindings.*;
  
  public class Handler implements MyService.IHandler {
      // ...
  }
  
  public class ClassA implements MyService.IClassA {
      // ...
  }
  
  public class ClassB implements MyService.IClassB {
      // ...
  }

For the code of a full server, refer to the :ref:`demos section <topic-demos>`.

You can use your favorite editor to generate all the necessary boilerplate 
code, or use the auto-generated *stub file*: when you generate the code with 
:ref:`agnosc <tool-agnosc>`, you will also find a file named ``MyService.stub`` 
(where ``MyService`` is the name of your service) in the same directory as the
rest of the generated code. This file contains a **skeleton implementation** 
of a server, and it's really easy to start from there.


Built-in Servers
----------------
Once you've implemented your **service**, it's time to expose it as a 
**server**. A server, as you might imagine, is a process that accepts incoming
connections from clients and handles them -- exposing the service behind it.

``libagnos`` comes with three flavors of servers built in:

* ``SimpleServer`` - a simple, single-threaded server, which can handle only
  a single connection at any point of time.
* ``ThrededServer`` - a simple multi-threaded server that creates a thread
  per incoming connection.
* ``LibraryModeServer`` - a single-shot server used for
  :ref:`Library Mode<doc-libmode>`. It's not likely that you'll need to
  use it directly -- it's usually handled through the ``CmdlineServer``.

Here's an example of setting up a ``ThreadedServer`` server, listening on
``localhost:12345``:

.. code-block:: java

  import static agnos.Servers.ThreadedServer;
  import static agnos.TransportFactories.SocketTransportFactory;
  
  //...
  
  public static void main(String[] args) {
      ThreadedServer server = new ThreadedServer(
              new MyService.ProcessorFactory(new MyHandler()),
              new SocketTransportFactory("localhost", 12345));
      try {
          server.main(args);
      } catch (Exception ex) {
          ex.printStackTrace(System.err);
      }
  }

.. _server-cmdline-args:

Aside from this, you will find the ``CmdlineServer`` class, which handles the 
standard command-line arguments and dispatches the selected server. 
You can select the server by passing ``-m MODE``, where ``MODE`` is one of 
``lib``, ``simple``, or ``threaded``; the ``simple`` and ``threaded`` 
modes also require that you pass ``-p TCP_PORT_NUMBER``, and optionally accept
``-h HOSTNAME``. The default mode is ``simple``, and the default hostname is 
``localhost``.

The ``CmdlineServer`` is used as follows:

.. code-block:: java

  import agnos.Servers.CmdlineServer;
  
  //...
  
  public static void main(String[] args) {
      CmdlineServer server = new CmdlineServer(
              new MyService.ProcessorFactory(new MyHandler()));
      try {
          server.main(args);
      } catch (Exception ex) {
          ex.printStackTrace(System.err);
      }
  }

As you can see, it takes care of almost everything related to setting up the
server and handling command-line arguments.

And here are some examples of invoking a ``CmdlineServer``-based server:
* ``myserver.exe -p 12345``
* ``myserver.exe -m threaded -p 12345 -h localhost``
* ``myserver.exe -m lib``


Implementing a Custom Server
----------------------------
It is well known that the built-in servers are very simplistic. As such, you 
may want to write custom servers for specialized cases (e.g., a ThreadPool 
server, controlling timeouts, quality of service, authentication, etc.). 
The library, of course, can't do all this for you (as part of the "mechanisms,
not policies" approach), but leaves the door open for custom implementations.

Basically, all you need in order to serve a connection is an 
``IProcessorFactory`` instance and an ``ITransportFactory`` instance.
The following boilerplate is basically enough:

.. code-block:: java

  void serve(ITransportFactory transportFactory, IProcessorFactory processorFactory) {
      ITransport transport = transportFactory.accept();
      BaseProcessor processor = processorFactory.create(transport);
      try {
          while (true) {
              processor.process();
          }
      }
      catch (EOFException ex) {
          // pass
      }
  }

This notion is already encapsulated into the ``BaseServer`` class. The easiest
and preferred way to implement a custom service is to derive from this class
and implement you own ``serveClient`` method. You can refer to the code to see
how it's done. However, if you require finer control on the serving process, 
you're welcome to write your own server from scratch.



