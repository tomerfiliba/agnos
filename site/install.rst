Installing Agnos
================

Compiler
--------
The ``agnos_compiler`` is a ``python`` package, so obviously you will need
to have `python installed <http://python.org/download/>`_. If you're running
on Windows, you can next-next-next your way with executable installer; 
otherwise, install it like any other python package: extract the 
``tar.gz`` (or ``zip``) and run ::

  $ python setup.py install       # you might need to sudo that command

For more info, refer to `Installing Python Modules <http://docs.python.org/install>`_

**Dependencies:** 

* `python <http://python.org/download/>`_ 2.6 or 3.0 and up.

------------------------------------------------------------------------------

Library
-------
``libagnos`` is provided as a set of independent libraries, for each target
language. If you'd wish writing a client in language X and a server in 
language Y, you'll need ``libagnos`` for both language X and language Y.

------------------------------------------------------------------------------

``C++``
"""""""

The ``C++`` implementation of the protocol is provided as in a source-only 
distribution (not precompiled), becuase ``C++`` has no standard ABI.

You can either compile the code into a library (which depends on your compiler),
or add it to your project directly. Don't forget to set the include path so
that ``#include <agnos.hpp>`` works.

.. note::
  In order to produce an executable, you will need to link with
  ``boost_thread``, ``boost_date_time``, ``boost_iostreams`` and 
  ``boost_system``

**Dependencies:**:

* A modern ``C++`` toolchain, compatible with Boost (``g++``, 
  *VisualStudio 2003* and up, etc.) 

* The `Boost <http://www.boost.org/>`_ library, version 1.40 and up.

  * *Windows users*: you can download 
    `compiled versions of Boost <http://www.boostpro.com/download/>`_

* *Optionally*: `Boost::Process <http://www.highscore.de/boost/process/>`_.
  This nice library allows executing child processes in a cross-platform manner.
  Sadly, though, it is not yet officially included in Boost, so you have to 
  install it separately.
   
  * It's a header-only library. Simply 
    `download the zip <http://www.highscore.de/boost/process.zip>`_ and extract 
    it to where your Boost include directory is (e.g., ``/usr/include/boost``).
  
  * You can specify in build-time whether this library is supported
    by defining ``BOOST_PROCESS_SUPPORTED`` (or not defining it)

* *Optionally*: The `scons build system <http://www.scons.org/>`_; ``libagnos-cpp``
  uses scons to build itself; of course you can use whatever build system 
  you like.

------------------------------------------------------------------------------

``C#``
""""""

The recommended way is to download the latest ``Agnos.dll``, and either 
`install it into the GAC <http://msdn.microsoft.com/en-us/library/dkkx7f79.aspx>`_
or explicitly reference it in your project. Alternatively, you can download 
the source and build it on your own.

**Dependencies:** 

* `.NET Framework <http://www.microsoft.com/net/>`_ 3.0 and up
  or `mono <http://mono-project.com/Main_Page>` 2.6 and up.

------------------------------------------------------------------------------

``java``
""""""""

The recommended way is to download the latest ``agnos.jar``, and either put
it in your ``JAVAPATH``, or explicitly reference it in your project.
Alternatively, you can download the source and build it on your own.

**Dependencies:** 

* `JDK <http://www.oracle.com/technetwork/java/javase/downloads/index.html>`_ 
  1.5 (also known as "java 5") and up

* *Optionally*: The `scons build system <http://www.scons.org/>`_; 
  ``libagnos-java`` uses scons to build itself; of course you can use 
  whatever build system you like.

------------------------------------------------------------------------------

``python``
""""""""""

``libagnos-python`` is a normal python package, which is accessed as 
``import agnos``. If you're running on Windows, you can next-next-next 
your way with executable installer; otherwise, install it like any other 
python package: extract the ``tar.gz`` (or ``zip``) and run ::

  $ python setup.py install       # you might need to sudo that command

For more info, refer to `Installing Python Modules <http://docs.python.org/install>`_

**Dependencies:** 

* `python <http://python.org/download/>`_ 2.6 or 3.0 and up.

