Tool Chain
==========

This page lists all the command-line tools provided with Agnos.

.. agnosc:

``agnosc``
----------
``agnosc`` is the Agnos Compiler command-line tool. It takes an IDL file (in
XML format) and generates the language bindings for the target language. 
Usage::
  
  agnosc -t TARGET [-o OUTDIR] idlfile.xml

Where ``TARGET`` is one of

* ``python`` (or ``py``) - generate ``python`` bindings
* ``java`` - generate ``java`` bindings
* ``cpp`` (or ``c++``) - generate ``C++`` bindings
* ``csharp`` (or ``cs``, ``c#``) - generate ``C#`` bindings
* ``doc`` - generate HTML documentation from the IDL

``OUTDIR`` is the directory where the bindings are created. If not given, 
they are created in the same directory as the input file (``idlfile.xml``).
A common practice is to use ``-o .`` to create the bindings in the working
directory.

.. _agnosrc-py:

``agnosrc-py``
--------------



