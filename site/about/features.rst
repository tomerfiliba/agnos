.. _doc-features:

Features
========
* **Cross-language**: interoperate seamlessly between ``java``, ``C#``, ``C++``,
  and ``python``.

* **Cross-platform**: relies only on cross-platform libraries and tools, and 
  the protocol itself is platform-agnostic.

* **SSL integration**: integrates with each language's SSL facilities to
  enable encrypted and authenticated sessions.

* **Lightweight and efficient**: Agnos uses a compact binary protocol and 
  supports point-to-point connectivity (no need to set up name servers, 
  web servers, URLs, etc.).

* :ref:`doc-srcgen`: Generate :ref:`doc-idl` specifications from in-code comments; 
  only one file to edit

* :ref:`RESTful front-end <doc-restful>`: unsupported languages can use Agnos-exposed
  services in a `RESTful <http://en.wikipedia.org/wiki/REST>`_ manner, 
  assuming they have HTTP client-side libraries.

* **Multiple topologies**:

  * **Direct socket connection**: clients connect directly to a listening socket
  
  * **HTTP Tunneling**: clients can tunnel the protocol over HTTP, sending 
    requests to a web server and have it forward the request to the Agnos 
    service. This is useful in environments that require integration with a 
    web server, or to cross firewalls.
  
  * :ref:`doc-libmode`: instead of setting up a server, you can spawn a server 
    process and connect to it -- in one line of code! This is useful when you
    have a library, written in one language, which you want to make use of 
    from another language.

* **Open Source**: :ref:`Apache license <doc-license>`


Planned Features
================
You can see the most up-to-date planned features and targets on our
`issue tracker <http://github.com/tomerfiliba/agnos/issues>`_. It's also 
possible to comment or vote on features, and we will do our best to use
this input for decide on our :ref:`road map <doc-roadmap>`:

Features
--------
* `Planned Features <http://github.com/tomerfiliba/agnos/issues/labels/planned%20features>`_ -
  features which we plan to support in the near future.

* `Optional Features <http://github.com/tomerfiliba/agnos/issues/labels/optional%20features>`_ - 
  features which are not likely to be supported in the near future; these are 
  more of ideas we toy with, but we'd love input on.

Targets
-------
.. note::
   A note on terminology: the word *target* refers to a *target language*
   of the Agnos tool-chain, meaning a language for which ``libagnos`` has been
   implemented, and the Agnos compiler can generate binding code for.

We would ultimately want to support as many target languages as possible, but
it won't happen soon. Any help in adding support for these languages (and 
possibly others) to Agnos would be greatly appreciated!

* `Planned Targets <http://github.com/tomerfiliba/agnos/issues/labels/planned%20features>`_ - 
  languages we plan support for. 

* `Optional Targets <http://github.com/tomerfiliba/agnos/issues/labels/optional%20features>`_ - 
  languages we would like to support, but are lacking the manpower to implement.


