##############################################################################
# Part of the Agnos RPC Framework
#    http://agnos.sourceforge.net
#
# Copyright 2011, International Business Machines Corp.
#                 Author: Tomer Filiba (tomerf@il.ibm.com)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
##############################################################################

try:
    from cStringIO import StringIO
except ImportError:
    from io import BytesIO as StringIO
try:
    from httplib import HTTPConnection, HTTPSConnection
except ImportError:
    from http.client import HTTPConnection, HTTPSConnection
try:
    from urlparse import urlparse
except ImportError:
    from urllib.parse import urlparse
from .transports import Transport
from . import packers


class HttpRequest(object):
    def __init__(self, conn, path, method="POST"):
        self.conn = conn
        self.path = path
        self.method = method
        self.headers = {}
    def __getitem__(self, key):
        return self.headers[key]
    def __setitem__(self, key, value):
        self.headers[key] = value
    def send(self, body):
        self.conn.request(self.method, self.path, body, self.headers)
        return self.conn.getresponse()


class HttpClientTransport(Transport):
    def __init__(self, url):
        Transport.__init__(self, None, None)
        self.url = url
        parsed = urlparse(url)
        self.urlprot = parsed.scheme.lower()
        self.urlhost = parsed.netloc
        self.urlpath = parsed.path
        self.conn = None

    def close(self):
        self.infile = None
        self.outfile = None

    def _build_request(self):
        if self.conn is None:
            if self.urlprot == "http":
                self.conn = HTTPConnection(self.urlhost)
            elif self.urlprot == "https":
                #TODO: key_file, cert_file, strict
                self.conn = HTTPSConnection(self.urlhost)
            else:
                raise ValueError("invalid url protocol: %r" % (self.urlprot,))
            self.conn.connect()
        req = HttpRequest(self.conn, self.urlpath)
        req["Content-type"] = "application/octet-stream"
        return req

    def begin_read(self, timeout = None):
        if not self.infile:
            raise IOError("begin_read must be called only after end_write")
        return Transport.begin_read(self, timeout)

    def end_read(self):
        self._assert_rlock()
        self.infile = None
        self._rlock.release()

    def end_write(self):
        self._assert_wlock()
        data = "".join(self._write_buffer)
        del self._write_buffer[:]
        if data:
            outstream = StringIO()
            packers.Int32.pack(len(data), outstream)
            packers.Int32.pack(self._write_seq, outstream)
            prefix = outstream.getvalue()
            req = self._build_request()
            self.infile = req.send(prefix + data)

        self._wlock.release()









