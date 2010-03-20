class Server(object):
    def __init__(self, handler, transport_factory):
        self.handler = handler
        self.transport_factory = transport_factory
    
    def serve(self):
        raise NotImplementedError()


class StdioServer(Server):
    pass

class SimpleServer(Server):
    def serve(self):
        self.transport_factory.open()
        while True:
            client = self.transport_factory.accept()
            while True:
                self.handler.process(client)
            client.close()
        self.transport_factory.close()








