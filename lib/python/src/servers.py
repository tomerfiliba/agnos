import threading


class BaseServer(object):
    def __init__(self, processor, transport_factory):
        self.processor = processor
        self.transport_factory = transport_factory
    
    def serve(self):
        while True:
            trans = self.transport_factory.accept()
            self._handle_client(trans)

    def _handle_client(self, transport):
        instream = transport.get_input_stream()
        outstream = transport.get_output_stream()
        
        try:
            while True:
                self.processor.process(instream, outstream)
        except EOFError:
            pass
    

class SimpleServer(BaseServer):
    pass


class ThreadedServer(BaseServer):
    def _handle_client(self, transport):
        t = threading.Thread(target = BaseServer._handle_client, args = (self, transport))
        t.start()














