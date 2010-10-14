About
=====
**Agnos** is developed by the *Host Side Group* at `IBM <http://www.ibm.com>`_ `XIV <http://www.xivstorage.com>`_, 
to provide our end users the ability to interoperate with our products 
(written mainly in `python <http://www.python.org>`_) from a variety of other 
languages. We spent time researching existing solutions, but all failed to 
meet our needs, either technologically or because of their overall complexity 
and overhead. 

The best candidate we came across was `Apache Thrift <http://incubator.apache.org/thrift/>`_, 
but it lacked object-oriented capabilities. Trying to not reinvent the wheel, 
we sought to augment this limitation by writing a "preprocessor" for Thrift 
that converts classes and methods to plain functions, hoping to eventually get 
it incorporated into Thrift. However, after some time and experimentation, 
it became clear this approach was not progressing well, and in April 2010, 
Agnos was born.

Agnos is loosely modeled after Thrift, both in its architecture and terminology, 
but the two projects do not share any code. Realising the open source community's
need for such a product, IBM has decided to contribute the code to open source,
under the :doc:`Apache License <license>`. 

The project is being developed and maintained by *Tomer Filiba* 
(``tomerf`` at ``il`` dot ``ibm`` dot ``com``).

.. note::
  Please do not send Agnos-related emails to my personal address -- I will not
  respond to them. See :doc:`contact` for more info.

