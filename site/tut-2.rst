Part 2: By-Value and By-Reference
=================================

The :doc:`first part <tut-1>` of the tutorial has introduced you to the 
:ref:`Agnos Compiler <tool-agnosc>`, how to implement a basic server,
and how to write a simple client. We have not delved too deeply into the
syntax and semantics of the IDL and its the different elements, since assumed 
it's self-explanatory enough (of course you can refer to the 
:doc:`reference documentation <idl>` for more info). 

In this part we'll learn more about three important constructs: **records**, 
**classes**, and **exceptions**, and the difference between passing objects
:ref:`By-Value and By-Reference <concepts-by-val-by-ref>`. 

.. note::
   As with the first part, this tutorial is not an exhaustive reference either.

Records
-------
:ref:`Records <idl-record>` are basically a collection of named fields, much
like ``struct`` in ``C``. They hold structured, heterogeneous information, and
are passed **by value**. This means that when they are sent over-the-wire,
they are `serialized <http://en.wikipedia.org/wiki/Serialization>`_
to bytes on one side and then reconstructed on the other. This essentially
means you end up with an identical **copy** of the original object, and 
there's no way to tell them apart.

Agnos automatically generates records (usually as classes) in the target 
language.


Classes
-------
:ref:`Classes <idl-record>` represent stateful objects, which consist of 
**attributes** (or *properties*) and **methods**. Generally speaking, the 
attributes represent the internal state of the object, and the methods allow 
you to alter it.

Instances of classes, by definition, are not *simple values* in the sense that
they cannot be copied. For example, an object that represents an open file 
handle cannot be copied to the other side... it's internal state may consist 
of a single integer (file handle), but copying this integer to the other
side is completely meaningless.

To solve that problem, of passing objects that may only exist in a defined
scope, Agnos employs passing objects **by reference**: Instead of copying the 
object (which is meaningless), an identifier that uniquely represents the
object is sent to the other side (normally the client). Then, the client can
invoke the methods of that object by passing this unique identifier back to
the server.

To simplify handling this identifier, proxy instances are created on the 
client-side. These proxies have the same "looks and feel" of the remote 
object, and they work by relaying all local operations to it.

.. note::
  In the current architecture, objects may "live" only on the server-side, 
  and proxies exist solely on the client-side. This means the two parties are
  not symmetrical. Future versions of Agnos may support symmetrical servers 
  and clients.

On the server-side, Agnos normally generates classes as interfaces in the 
target language, and leaves the implementation to the service itself. On the
client side, proxies are automatically generated.
 

Exceptions
----------
Exceptions are much like records (being a collection of fields), only they 
derive from the appropriate exception class of the target language. 
Exceptions are normally used to represent exceptional (erroneous) situations
which require handling the problem or terminating. 

Example
-------
Consider the following IDL:

.. code-block:: xml

    <service name="RemoteFiles">
        <enum name="FileMode">
            <member name="read" />
            <member name="write" />
            <member name="readwrite" />
        </enum>
        
        <class name="File">
            <attr name="filename" type="str" set="no">
            <attr name="mode" type="FileMode" set="no">
            
        </class>
    </service>


































