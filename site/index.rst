.. toctree::
   :hidden:
   
   contents


Welcome
=======
**Agnos** is a *cross-language*, *cross-platform*, *lightweight* RPC framework with 
support for passing objects *by-value* or *by-reference*. Agnos is meant to 
allow programs written in different languages to easily interoperate, by 
providing the needed bindings (glue-code) and hiding all the details from 
the programmer. The project essentially servers the same purpose as existing 
technologies like `SOAP <http://en.wikipedia.org/wiki/SOAP>`_, `WSDL <http://en.wikipedia.org/wiki/WSDL>`_,
`CORBA <http://en.wikipedia.org/wiki/CORBA>`_, and others, but takes a 
**minimalistic approach** to the issue at hand.

Unlike the aforementioned technologies, which tend to require integration with
*web servers*, using verbose XML-based protocols on top of *textual* transports 
(HTTP), often also requiring complex topologies (such as *name servers* for
registering objects, etc.) -- Agnos is designed to be **simple, efficient, 
and straightforward**, allowing for direct communication between two ends 
using a compact binary protocol. You can **read more** :doc:`about Agnos <about>`.

Key Features
============
* **Interoperate** between ``python``, ``C#``, ``java``, and ``C++``
* **Cross-platform**
* Operates locally or over a network, using sockets directly, or over HTTP
* :doc:`srcgen` generates IDL from **special comments within your source 
  code** -- only a single place to edit!
* Lightweight, speedy, and efficient
* :doc:`library-mode` - connect to a spawned server process in one line of code
* Released under the :doc:`Apache License <license>`

For the full list, see :doc:`features and future plans <features>`.

Getting Started
===============
If you're ready to see go, check out our :doc:`documentation` page.

Teaser
======
To demonstrate what we mean by **easy, efficient, and straightforward**, 
here's a simple :doc:`IDL <idl>` that defines a remote file access service: 

.. code-block:: xml

  <service name="RemoteFiles">
      <enum name="FileMode">
          <member name="R" />
          <member name="W" />
      </enum>
  
      <class name="File">
          <attr name="name" get="yes" set="no" />
          <method name="close" type="void" />
          <method name="read" type="buffer">
              <doc>read up to 'count' bytes from the file. an empty string means EOF</doc>
              <arg name="count" type="int32" />
          </method>
          <method name="write" type="void">
              <doc>writes 'data' to the file</doc>
              <arg name="data" type="buffer" />
          </method>
      </class>
  
      <func name="open" type="File" />
          <arg name="filename" type="string" />
          <arg name="mode" type="FileMode" />
      </func>
  </service>

This should be pretty obvious: this IDL defines an enum (``FileMode``), 
a class (``File``) with a single attribute and the three methods, 
and a function (``open``) that returns ``File`` instances. 

Using this service from ``python``, for instance, couldn't get easier. Just run ::

  $ agnosc -t python remotefiles.xml

to generate the language bindings (which will be named ``RemoteFiles_bindings.py``), 
and then

.. code-block:: python
    
  import RemoteFiles_bindings as RemoteFiles
  
  conn = RemoteFiles.Client.connect("somehost", 12345)
  
  f = conn.open("/tmp/foo", RemoteFiles.FileMode.W)
  f.write("hello kitty\n")
  f.close()

Implementing the service is a little lengthy, naturally, but very trivial too.
To see how that's done, check out the :doc:`demo <demo-1>`.


