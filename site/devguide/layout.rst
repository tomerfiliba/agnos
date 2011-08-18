.. _doc-project-layout:

Project Layout
==============
This section attempts to provide an overview of the Agnos toolchain and serves as
an introduction to developers working on the toolchain. It is probably of little
interest to end-users.

Targets
-------
Agnos uses the term *target* to refer to a programming language that's supported
by the toolchain. Targets consist of two parts: **compiler target** (the code-generator, 
the part that's responsible for transforming the service's IDL into the language
bindings), and **libagnos** (an implementation of the Agnos protocol, transport abstractions,
and various otehr utilities).

See :ref:`doc-impl-targets` for through details.


Protocol
--------
Agnos uses a simple and efficient binary protocol that's described in detail in the
:ref:`doc-protocol`. When you come to implementing ``libagnos`` for your target language,
you have to carefully follow the protocol: this includes the wire-format, packer IDs,
implement all commands and info queries, etc.


Building
--------
The Agnos compiler is written in python, and therefore requires no building. The
``libagnos`` implementation, however, would usually require some integration with 
a build system (``make``, ``ant``, ``scons``, etc.), to generate the modules the 
end user would link with. 

Alternatively, you may also provide an "installer" for your package, e.g., a 
python ``egg`` or a ruby ``gem``, so users could use a ``gem install libagnos`` 
or something in that spirit.

For compiled languages, I would recommend using `scons <http://scons.org/>`_: I find
it the easiest, most powerful and most comprehensive build system out there.


Testing
-------
Each target should have proper unit-tests. We place unit tests under the ``tests/`` 
directory, under which you can create a directory for your implementation and
write your unit tests.

All existing tests use ``tests/features.xml`` as their test case: it's an IDL file
that (supposedly) includes all the features one can use in an IDL. Each target
language includes an implementation of that IDL and a client that invokes the
test scenario.

Of course you may write more comprehensive tests, but we use ``features.xml`` as the
base-line for every implementation.


Documentation
-------------
Your implementation of ``libagnos`` should be fully-documented using a suitable 
documentation framework that supports the target language. For instance, for python 
we're using doc-strings (in ReST format) that `Sphinx <sphinx.pocoo.org>`_ can process,
for java we use ``javadoc``, etc.

The target audience of this documentation is the end-users of Agnos, i.e., people
who are consuming an Agnos service (clients) or implementing services (server-side).
For instance, a user programming in C# using Visual Studio would love to see some
pop-up documentation when he types ::

.. code-block:: C#
    
    HeteroMap h = new HeteroMap();
    h.Add(

The toolchain's docs (found in the ``site/`` directory) should also be updated, to reflect
the changes. For instance, if you added a ``ruby`` target, don't forget to update
:ref:`doc-features` and ``index.rst``.















