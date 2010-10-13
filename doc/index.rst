.. toctree::
  :hidden:
  
  features
  getting-started
  tutorial
  idl
  about
  license
  contribution


Agnos
=====
**Agnos** is a cross-language, cross-platform, lightweight RPC framework with 
support for passing objects *by-value* or *by-references*. Agnos is meant to 
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
using a compact binary protocol.

If your are interested, please to read more :doc:`about Agnos <about>`. 
Also, be sure to have a look at the :doc:`getting-started` guide and the 
:doc:`tutorial`.

Features
--------
* Supports ``python``, ``C#``, ``java``, and ``C++``
* Operate locally or over a network, using sockets directly or over HTTP
* *Library mode* - spawn a server process and connect to it (in one line of code!)

Read more about :doc:`features and future plans <features>`.

A Quick Example
---------------
Here's a simple :doc:`idl` specification, for remote file access, that 
demonstrates what we mean by **easy, efficient, and straightforward**:

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
              <doc>read up to 'count' bytes from the file. empty string means EOF</doc>
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
Let's say that we want to use (as a client) this service from ``python``. 
First we'll need to run ``$ agnosc -t python remotefiles.xml`` to generate the 
python bindings (``RemoteFiles_bindings.py``), and then it's as simple as that:

.. code-block:: python
    
  import RemoteFiles_bindings as RemoteFiles
    
  conn = RemoteFiles.Client.connect("hostname", 12345)
    
  f = conn.open("/tmp/foo", RemoteFiles.FileMode.W)
  f.write("hello kitty\n")
  f.close()

A ``java`` / ``C#`` / ``C++`` client would be a little more verbose, naturally, 
but even then, it would require only one line of boilerplate. 
Implementing the server is a bit lengthy, but very simple and to-the-point as well.

Contact
-------
Please use our `mailing list <http://groups.google.com/group/agnos>`_ for questions, 
bug reports, feature requests/suggestions, and general discussion.


