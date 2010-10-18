Welcome
=======
**Agnos** is a cross-language, cross-platform, lightweight RPC framework with 
support for passing objects *by-value* or *by-reference*. Agnos is meant to 
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
using a compact binary protocol. You can **read more** :doc:`about Agnos <about>`.

Get Me Going
============
:doc:`Get the Feel of Agnos <teaser>`

:doc:`Download and Installation Instructions <install>`
 
:doc:`Hands-On Tutorial <tutorial>`
 
:doc:`Real-Life Demos <demos>`

:doc:`Full Documentation <documentation>`

:doc:`Contact Info and Bug Reports <contact>`

Key Features
============
* **Interoperate** between ``python``, ``C#``, ``java``, and ``C++``
* **Cross-platform**
* Operates locally or over a network, using sockets directly or over HTTP
* Generate IDL from **special comments within your source code** -- only one place to edit
* Lightweight, speedy, and efficient
* :ref:`library-mode` - connect to a spawned server process in one line of code
* Released under the :doc:`Apache License <license>`

For more info, refer to the :doc:`features and future plans <features>`.



