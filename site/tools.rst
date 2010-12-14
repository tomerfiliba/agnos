Tool-chain
==========
This page describes the command-line tools that make up the agnos tool-chain.

------------------------------------------------------------------------------ 

.. _tool-agnosc:

``agnosc``
==========
The Agnos compiler. This is the tool that takes an IDL file 
(in :doc:`XML format <idl>`) and generates the language bindings for the 
target-language. 

Usage:
------
``$ agnosc -t TARGET [-o OUTDIR] IDLFILE...``

``-t TARGET``
^^^^^^^^^^^^^
Required.

The desired target-language. ``TARGET`` may be one of:

* ``doc`` -- generates a javadoc-like HTML file, describing the service
* ``py`` / ``python`` -- generates ``python`` bindings
* ``java`` -- generates ``java`` bindings
* ``csharp`` / ``c#`` / ``cs`` -- generates ``C#`` bindings
* ``cpp`` / ``c++`` -- generates ``C++`` bindings

``-o OUTDIR``
^^^^^^^^^^^^^
Optional.

Specifies the output directory where the generated code will be placed.
By default, the parent directory of the IDL file is used,.

``IDLFILE``
^^^^^^^^^^^
Required.

The IDL file to process. At least one file is required. If multiple files are 
provided, each will be processed independently (with the same `TARGET`` and 
``OUTDIR`` settings).

Example
-------
``$ agnosc -t java -o /tmp/my-bindings /path/to/my/idl.xml``

------------------------------------------------------------------------------

.. _tool-agnosrc-py:

``agnosrc-py``
==============
The Pythonic :doc:`srcgen` tool. It takes a source directory (``SRCDIR``), 
which contains a python package, scans all the python files within it 
(recursively) for special comments, and creates the following files:

* IDL file (in XML format) that holds all the information gathered from the 
  in-line comments.
* Python bindings of the service
* An executable python server file that exposes the service

For more info, refer to :doc:`srcgen`.

Usage:
------
::

  $ agnosrc-py [-o OUTDIR] [-p PKGNAME] [--idlfile=IDLFILENAME] 
               [--serverfile SVRFILENAME] [--historyfile=HISTFILE] SRCDIR


``-o OUTDIR``
^^^^^^^^^^^^^
Optional.

Specifies the output directory, where the generated code will be placed.
By default, ``SRCDIR`` itself is used, so it is advisable to set the ``-o``
option to some other directory.

``-p PKGNAME``
^^^^^^^^^^^^^^
Optional.

Specifies the package name. By default, the name is assumed to be the ``basename``
of ``SRCDIR``. For instance, if ``SRCDIR`` is ``/foo/bar/lala``, the package 
name is assumed to be ``lala``. 

The package name is necessary for the auto-generated server, where it's used 
in ``import`` statements. If your package is to be imported by a different 
name, you should set this option accordingly.

``--idlfile=IDLFILENAME``
^^^^^^^^^^^^^^^^^^^^^^^^^
Optional.

Specifies the name of the generated IDL file. By default, the name is of the 
service is used. For example, if the service name (as defined by ``@service``)
is ``foobar``, the generated IDL file will be named ``foobar.xml``, and placed
in ``OUTDIR``.

``--serverfile=SVRFILENAME``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Optional.

Specifies the name of the auto-generated server.
By default, the name is of the service is used, suffixed by ``_server.py``.
For example, if the service name (as defined by ``@service``) is ``foobar``, 
the generated server file will be named ``foobar_server.py``, 
and placed in ``OUTDIR``.

``--historyfile=HISTFILE``
^^^^^^^^^^^^^^^^^^^^^^^^^^
Optional.

The name of the history file to use. By default, ``IDLFILENAME`` is used, 
suffixed by ``_history``. 

The history file is used for multi-versioning, as a place to store the IDs
that were assigned to IDL elements, so that later invocations of ``srcgen`` 
would use the same IDs for the same elements. This is crucial for 

The history file is a simple text file where each line takes the form of 
``<ID NUMBER>   <NAME>``. It's basically a a dictionary that maps fully-qualified
entity names to their previously assigned IDs. 

``SRCDIR``
^^^^^^^^^^
Required.

The source directory to use. This is the root directory of the python package
that you wish ``srcgen`` to process, i.e., the directory that holds the 
outer-most ``__init__.py`` file.

This directory will be recursively scanned for ``*.py`` files, all of which 
will be processed by ``srcgen``.


Example
-------
``$ agnosrc-py /path/to/my/package -o /tmp/my/package -p ub3rpkg``



