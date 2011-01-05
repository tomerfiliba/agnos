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

import sys
import os
import threading
from optparse import OptionParser
from .transports import SocketTransportFactory


def _serve_client(processor):
    try:
        while True:
            processor.process()
    except EOFError:
        pass
    finally:
        processor.transport.close()


class BaseServer(object):
    def __init__(self, processor_factory, transport_factory):
        self.processor_factory = processor_factory
        self.transport_factory = transport_factory
    
    def close(self):
        self.transport_factory.close()
    
    def serve(self):
        while True:
            trans = self.transport_factory.accept()
            processor = self.processor_factory(trans)
            self._serve_client(processor)
        
    def _serve_client(self, processor):
        raise NotImplementedError()

class SimpleServer(BaseServer):
    def _serve_client(self, processor):
        _serve_client(processor)

class ThreadedServer(BaseServer):
    def _serve_client(self, processor):
        t = threading.Thread(target = _serve_client, args = (processor,))
        t.start()

class LibraryModeServer(BaseServer):
    def serve(self):
        sys.stdout.write("AGNOS\n%s\n%d\n" % (self.transport_factory.host, self.transport_factory.port))
        sys.stdout.flush()
        sys.stdout.close()
        trans = self.transport_factory.accept()
        self.transport_factory.close()
        processor = self.processor_factory(trans)
        _serve_client(processor)

def server_main(processor_factory, mode = "simple", port = 0, host = "localhost"):
    parser = OptionParser(conflict_handler="resolve")
    parser.add_option("-m", "--mode", dest="mode", default=mode,
                      help="server mode (simple, threaded, library)",  
                      metavar="MODE")
    parser.add_option("-p", "--port", dest="port", default=port,
                      help="tcp port number; 0 = random port", metavar="PORT")
    parser.add_option("-h", "--host", dest="host", default=host,
                      help="host to bind", metavar="HOST")
    parser.add_option("-l", "--log", dest="logfile", default=None,
                      help="log file to write to", metavar="FILENAME")

    options, args = parser.parse_args()
    if args:
        parser.error("server does not take positional arguments")
    options.mode = options.mode.lower()

    transport_factory = SocketTransportFactory(int(options.port), options.host)
    if options.mode == "lib" or options.mode == "library":
        s = LibraryModeServer(processor_factory, transport_factory)
    elif options.mode == "simple":
        if int(options.port) == 0:
            parser.error("must specify port for simple mode")
        s = SimpleServer(processor_factory, transport_factory)
    elif options.mode == "threaded":
        if int(options.port) == 0:
            parser.error("must specify port for threaded mode")
        s = ThreadedServer(processor_factory, transport_factory)
    else:
        parser.error("invalid mode: %r" % (options.mode,))
    try:
        s.serve()
    except KeyboardInterrupt:
        sys.stderr.write("server quits after SIGINT\n")
    except Exception:
        raise




