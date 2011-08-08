.. _doc-concepts:

Concepts
========
This section outlines some fundamental concepts and terms that are needs before 
delving into the rest of the documentation. Please do not skip this.

RPC
---
An RPC (Remote Procedure Call) framework, is a technology that allows different 
processes to communicate with one another, allowing one (usually the client) 
to invoke a remote function (that is executed on the server) and obtain its result. 
RPCs normally define the communication protocol between the two parties, 
a common type system, a serialization scheme that governs how each type is 
converted into raw bytes, and codes that represent successful or erroneous 
operation. Other than that, the RPC framework normally takes care of establishing 
the connection between the two parties and managing its lifetime. 
The purpose of the RPC layer is to hide all the details, so the two parties 
could communicate *programmatically* -- invoking functions, passing parameters,
obtaining return values, catching exceptions, etc.

Virtually all communication protocols are essentially degenerate forms of RPC:
they define all of the above, to a certain degree, but usually fail to hide the 
details well. For instance, **HTTP** defines a ``GET`` function that takes 
various parameters, defines a simple type system (strings, dates, numbers, 
mime-types) and weak serialization rules (``Base64``, ``form-urlencoded``), 
success (200) and error (404, 500) codes, connection management (timeouts, 
reconnect) -- this can in fact be seen as a "half-baked RPC framework". 
Not only that, but it has become the standard communication layer of the 
internet (disregarding the fact it's not suitable for many of the protocol
stacks built on top of it). 

Theoretically, all RPC frameworks are capable of bridging the language boundary,
where one of the parties is written in language A and the other is written in 
language B -- but unless the framework was specifically designed to allow that, 
the resulting process is cumbersome and "unnatural". This is why you have to 
work so hard when using HTTP programmatically (it was simply not designed for
that).

.. _concepts-by-val-by-ref:

By-Value vs. By-Reference
-------------------------
Most RPC frameworks limit themselves to **values**, as opposed to **objects**.
Values are simply serailized to bytes and sent over-the-wire, where the value
is reconstructed on the other side, the details of which may be quite complicated.
Simple all complex, all values share one common property: they are **stateless**:
once a value has been passed to the other side, there are two *copies* of it,
one on each side. 

This model works well for many applications, but at some level of complexity
you are bound to run into a problem: how do you pass non-copyable objects? For
instance, open files, computer processes, sockets, entire file systems, and the 
list goes on. At this point, you require **passing objects by-reference**.

When passing an object by reference, only a unique identifier (normally an integer)
of this object is sent to the other side -- the actual object remains where it 
was (usually on the server). On the other side (i.e., the client), 
a **proxy object** is created to represent the remote one. This proxy object 
exposes the same methods and attributes as the remote object, making the two
compatible and interchangeable. The proxy object is actually a hollow shell
that simply forwards every operation that's done on it to the other side,
where it's actually performed, and the result is returned.

All in all, passing objects by-reference gives the client the illusion that
it "holds" the remote object (and can use it the same way), while the object
remains on the server. This allows "passing" stateful, very large, or otherwise 
non-copyable objects between the two sides, transparently. However, object 
proxying adds a performance penalty, since every operation requires a full 
round-trip to the server. If this happens every now and then, it shouldn't pose
a problem, but if it's done within a tight-loop (e.g., get the ``name`` attribute
of 10000 ``People`` objects), you might run into slow-downs. In such a case,
it's better to redesign the service, adding a new function or method, so the 
tight-loops occur efficiently on the server side.

Records vs. Classes
-------------------
Agnos separates the two notions (by-value vs. by-references) cleanly, by 
defining separates language constructs: *records* and *classes*. Records,
as the name implies, are orderd collections of attributes (or "fields") that 
are passed by-value; classes, on the other hand, pass by-reference.

.. note::
  All the :ref:`built-in types <doc-types>` pass by-value (except for *reference
  collections* -- ``reflist``, etc.)

Do not be confused though: records can contain attributes of by-reference type,
and classes can contain attributes of by-value type. This does not pose any 
problem. For instance:

.. code-block:: xml

  <record name="Address">
      <attr name="country" type="str" />
      <attr name="city" type="str" />
      <attr name="street" type="str" />
      <attr name="number" type="int" />
  </record>
  
  <class name="Person">
      <attr name="name" type="str" />
      <attr name="date_of_birth" type="date" />
      
      <attr name="address" type="Address" />  <!-- the type is a record -->
  </class>
  
  <record name="Family">
      <attr name="husband" type="Person" />   <!-- the type is a class -->
      <attr name="wife" type="Person" />
      <attr name="children" type="list[Person]" />
  </record>


Terminology
===========
* **Target Language**: refers to a language supported by the Agnos compiler,
  meaning the toolchain can generate the binding code for that language. 
* **Proxy Object** (also *proxy instance*): an object, created on the client
  side, that represents a remote object. The proxy object exposes the same 
  interface as the remote one, making the two compatible.






