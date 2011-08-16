.. _doc-over-http:

Agnos Over HTTP
===============

In order to cross firewalls more easily and integrate with existing web-servers,
Agnos provides a simple way to "tunnel" Agnos transportation over HTTP.

.. note::
   This feature is considered experimental and is currently only supported by
   the python and C# implementations. 

Agnos-over-HTTP employs a very straight-forward implementation: the client sends 
an HTTP request (a ``POST`` to some URL), setting all the usual HTTP headers 
(``content-type``, ``content-length``, etc.), where the HTTP payload is the 
Agnos-encoded request. ::

    GET /myservice HTTP/1.1
    Content-type: application/x-agnos
    Cotent-length: 1234
    Cookie: foobar
   
    <agnos request blob>

The HTTP server receives this request and (based on the URL) dispatches it to 
an Agnos server "behind the scenes". This Agnos server (unaware of the HTTP
proxying) simply processes the request and sends back the response, where
the HTTP server wraps it with the appropriate HTTP response headers and
sends it back to the client. ::

    HTTP/1.1 200 OK
    Content-type: application/x-agnos
    Cotent-length: 2345
    Set-Cookie: foobar
   
    <agnos response blob>

.. note::
   This modus-operandi requires that the HTTP server keeps an active connection
   to the Agnos server. The HTTP server also needs to associate a different
   Agnos connection with each client (but this can be done using cookies
   or different URLs). You may also want to add HTTP authentication to the
   process and HTTPS.
   
   However, how you choose to implement this is out of the scope (and 
   responsibility) of Agnos.

The client then strips the HTTP headers and continues to process the request
normally.

From the client's perspective, all of this wrapping/unwrapping process is
handled by the ``HttpClientTransport`` class.







