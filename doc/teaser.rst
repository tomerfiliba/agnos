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

Using this service from ``python``, for instance, is a piece of cake. Just run ::

  $ agnosc -t python remotefiles.xml

to generate the language bindings (``RemoteFiles_bindings.py``), and then

.. code-block:: python
    
  import RemoteFiles_bindings as RemoteFiles
  
  conn = RemoteFiles.Client.connect("somehost", 12345)
  
  f = conn.open("/tmp/foo", RemoteFiles.FileMode.W)
  f.write("hello kitty\n")
  f.close()

Implementing the service is a little more lengthy, naturally, but fear not! 
It's very simple too.

