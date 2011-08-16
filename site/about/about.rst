.. _doc-about:

About Agnos
===========
.. toctree::
   :maxdepth: 1
   :hidden:
   
   contact
   contrib
   license
   changelog
   roadmap

Agnos is developed and maintained by `IBM XIV <http://www.xivstorage.com>`_, 
at the *Host Side Group*, to allow our end users to utilize our products with 
ease, from a variety of programming languages. We develop Storage Array 
management APIs, mostly in ``python``, and we had to allow our clients 
(who use more "solid" languages, such as ``java`` or ``C++``), to natively 
invoke these APIs. 

The task of exposing hierarchal object-oriented APIs turned out rather complex, 
and we spent much time investigating the available, open, and standardized RPC 
technologies (e.g., `SOAP <http://en.wikipedia.org/wiki/SOAP>`_,
`CORBA <http://en.wikipedia.org/wiki/CORBA>`_, `ZeroC ICE <http://www.zeroc.com/ice.html>`_,
`Protocol Buffers <http://code.google.com/p/protobuf/>`_, and others). 
Sadly, all failed to meet our needs, being technologically inferior, 
topologically unmaintainable, or having licensing issues. The closest
contestant was `Apache Thrift <http://incubator.apache.org/thrift/>`_, which 
was lightweight and seemed to do everything we needed, except for passing 
objects by-reference.

Trying to reinvent the wheel as little as possible, we sought to augment 
Thrift's deficiency by a writing a preprocessor that converts class properties
and methods into "plain old functions", and then used Thrift to actually generate
the binding code. We planned to get this feature incorporated into the 
Thrift compiler, but with time it became clear that this approach is not 
progressing well, and in April 2010, Agnos was born.

As such, Agnos is loosely modeled after Thrift, both in its architecture and 
terminology. It is important to stress, however, that the two projects do not 
share code or are otherwise related, and that the Apache license (which Thrift 
is released under) allows *derivative works*. 


Open Source
-----------
IBM chose to open-source Agnos, under the :ref:`Apache License <doc-license>`, 
believing that such a project would do a great service to the open source 
community -- just as we would have wished to find a suitable open source
project instead of writing one from scratch.

We also hope this would help Agnos mature faster, receiving bug reports and
patches from users, maybe even new features. For more information, please
refer to the :ref:`doc-contrib`.


