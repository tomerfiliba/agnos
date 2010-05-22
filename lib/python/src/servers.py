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

    @classmethod
    def _serve_client(cls, processor, transport):
        instream = transport.get_input_stream()
        outstream = transport.get_output_stream()
        try:
            while True:
                processor.process(instream, outstream)
        except EOFError:
            pass

class SimpleServer(BaseServer):
    def _accept_client(self, transport):
        self._serve_client(self.processor, transport)

class ThreadedServer(BaseServer):
    def _accept_client(self, transport):
        t = threading.Thread(target = BaseServer._serve_client, args = (self.processor, transport))
        t.start()

class LibraryModeServer(BaseServer):
    def serve(self):
        sys.stdout.write("%s\n%d\n" % (self.transport_factory.host, self.transport_factory.port))
        sys.stdout.flush()
        sys.stdout.close()
        os.close(sys.stdout.fileno())
        trans = self.transport_factory.accept()
        self._handle_client(trans)

def server_main(processor):
    parser = OptionParser()
    parser.add_option("-m", "--mode", dest="mode", default="simple",
                      help="server mode (simple, threaded, library)",  
                      metavar="MODE")
    parser.add_option("-p", "--port", dest="port", default="0",
                      help="tcp port number; 0 = random port", metavar="PORT")
    parser.add_option("--host", dest="host", default="localhost",
                      help="host to bind", metavar="HOST")
    options, args = parser.parse_args()
    if args:
        parser.error("server does not take positional arguments")
    options.mode = options.mode.lower()

    transfactory = SocketTransportFactory(int(options.port), options.host)
    if options.mode == "lib" or options.mode == "library":
        s = LibraryModeServer(processor, transfactory)
    elif options.mode == "simple":
        s = SimpleServer(processor, transfactory)
    elif options.mode == "threaded":
        s = ThreadedServer(processor, transfactory)
    else:
        parser.error("invalid mode: %r" % (options.mode,))
    try:
        s.serve()
    except KeyboardInterrupt:
        sys.stderr.write("server quits after SIGINT\n")
    except Exception:
        raise




