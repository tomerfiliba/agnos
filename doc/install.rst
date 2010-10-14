Download
========
First you'll need to get the Agnos compiler: you can obtain "official" releases
from `sourceforge <http://sourceforge.net/downloads/agnos>`_, or browse (and clone)
our `git repository <http://github.com/tomerfiliba/agnos>`_. See the :doc:`download` page for 
details.

.. dependencies:

Dependencies
------------
The Agnos compiler itself depends on only on `python <http://www.python.org>`_,
and requires python 2.6 or up. 

In order to compile the generated bindings, you will need additional toolchains:
* ``java``: `JDK 1.5 <http://www.oracle.com/technetwork/java/javase/downloads/index.html>` and up
* ``C#``: Either `.NET 3.0 <http://www.microsoft.com/net/download.aspx>` and up 
  or `Mono 2.6 <http://www.mono-project.com/Main_Page>`_ and up 
* ``C++``: A modern C++ toolchain and the `Boost <http://www.boost.org/>`_ libraries (1.40 and up). 
  Windows users can get the library pre-compiled at http://www.boostpro.com/download/
  * Additionally, you may want to install `Boost::Process <http://www.highscore.de/boost/process/>`_,
    to enable the ``SubprocClient`` etc. For some reason, it's still not included 
    in Boost, and you have to install it separately. It's a header-only library 
    that you simply extract to your Boost include directory (e.g., ``/usr/include/boost``). 


Installation
============
Agnos is distributed as a zip package, which includes:
* ``agnos-compiler.tar.gz`` (or ``.exe`` or ``.egg``)
* ``agnos-python.tar.gz`` (or ``.exe`` or ``.egg``)
* ``agnos-cpp.tar.gz`` (or ``.zip``)
* ``agnos-java.tar.gz`` (or ``.zip``)
* ``agnos-java.jar``
* ``agnos-csharp.tar.gz`` (or ``.zip``)
* ``agnos-dotnet.dll``

 

If you downloaded the Windows installer, 
just run it and it will do the magic. Otherwise, you'll need to extract the 
tarball and run ``setup.py install``.

At this point, you should be able to pop up a python interpreter and type ::

  import agnos_compiler

without getting errors.

Agnos also installs two executable scripts: ``agnosc`` and ``agnosc-py``. You should
try running them, to make sure they are in your ``PATH``. If not, it's most likely
that you'll have to tweak your system's ``PATH``. On Windows, for example, you'll
need to add ``C:\Python26\Scripts``, or something like that.

Now you are good to go: the Agnos toolchain is installed, and you can generate bindings.
In order to compile, you will need the aforementioned :ref:`dependencies`, and 
the Agnos Protocol libraries. 


C++
===

Boost
-----


Boost::Process
--------------