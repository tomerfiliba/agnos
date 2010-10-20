Downloading Agnos
=================

Overview
--------
Agnos consists of two parts: ``agnos_compiler`` and ``libagnos``. The 
``agnos_compiler`` is a set of utilities that generate language-bindings from
:doc:`IDL specifications <idl>`. ``libagnos`` is a set of libraries that 
implement the Agnos protocol for the various languages supported by Agnos. 

In order to develop services with Agnos you will need the ``agnos_compiler``
and ``libagnos``. If you only wish to use a client of an Agnos service, 
you will only require ``libagnos`` (the compiler is of no use to you).

.. note::
  ``libagnos`` is also licensed under the Apache license, which means you can
  distribute a compiled ``libagnos`` with your product.


Releases
--------
You can find "official" releases on `sourceforge <http://sourceforge.net/downloads/agnos>`_
(choose the package formats that suite your operating system best)

Note that ``libagnos`` has separate packages for each target language, and 
naturally if you want language X to call language Y, you will need to install 
both libraries.

All the packages are provided in source form, while some are provided in 
binary form. Generally for ``mono``/``.NET`` and ``java``, downloading the
binary version would make more sense than having to compile them on your own.
For ``C++``, on the other hand, since there's no cross-compiler ABI, only
the source form is available.


Repository
----------
Agnos development takes place on `github <http://github.com/tomerfiliba/agnos>`_.
You will find there the master branch of Agnos (*possibly unstable*),
as well as tagged versions, which are considered stable.


Installation
------------
Continue to :doc:`Installing Agnos <install>`.





