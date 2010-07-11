import sys
import os
import threading
from optparse import OptionParser
from .transports import SocketTransportFactory


class BaseServer(object):
    def __init__(self, processor, transport_factory):
        self.processor = processor
        self.transport_factory = transport_factory
    
    def serve(self):
        while True:
            trans = self.transport_factory.accept()
            self._accept_client(trans)

    def _accept_client(self, transport):
        raise NotImplementedError()

    def _serve_client(self, transport):
        try:
            while True:
                self.processor.process(transport)
        except EOFError:
            pass
        finally:
            transport.close()

class SimpleServer(BaseServer):
    def _accept_client(self, transport):
        self._serve_client(transport)

class ThreadedServer(BaseServer):
    def _accept_client(self, transport):
        t = threading.Thread(target = self._serve_client, args = (transport,))
        t.start()

class LibraryModeServer(BaseServer):
    def serve(self):
        sys.stdout.write("%s\n%d\n" % (self.transport_factory.host, self.transport_factory.port))
        sys.stdout.flush()
        sys.stdout.close()
        trans = self.transport_factory.accept()
        self._serve_client(trans)

def server_main(processor, mode = "simple", port = 0, host = "localhost"):
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

    transfactory = SocketTransportFactory(int(options.port), options.host)
    if options.mode == "lib" or options.mode == "library":
        s = LibraryModeServer(processor, transfactory)
    elif options.mode == "simple":
        if int(options.port) == 0:
            parser.error("must specify port for simple mode")
        s = SimpleServer(processor, transfactory)
    elif options.mode == "threaded":
        if int(options.port) == 0:
            parser.error("must specify port for threaded mode")
        s = ThreadedServer(processor, transfactory)
    else:
        parser.error("invalid mode: %r" % (options.mode,))
    try:
        s.serve()
    except KeyboardInterrupt:
        sys.stderr.write("server quits after SIGINT\n")
    except Exception:
        raise




