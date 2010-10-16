#import agnos
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer 
import urlparse

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urlparse.urlparse(self.path)
        message = '\n'.join([
                'CLIENT VALUES:',
                'client_address=%s (%s)' % (self.client_address,
                                            self.address_string()),
                'command=%s' % self.command,
                'path=%s' % self.path,
                'real path=%s' % parsed_path.path,
                'query=%s' % parsed_path.query,
                'request_version=%s' % self.request_version,
                '',
                'SERVER VALUES:',
                'server_version=%s' % self.server_version,
                'sys_version=%s' % self.sys_version,
                'protocol_version=%s' % self.protocol_version,
                '',
                ]) 
        self.send_response(200)
        self.end_headers()
        self.wfile.write(message)


def run(host = "localhost", port = 8080):
    server = HTTPServer((host, port), Handler)
    server.serve_forever()


if __name__ == "__main__":
    run()

    #CLIENT VALUES:
    #client_address=('127.0.0.1', 64886) (podracer)
    #command=GET
    #path=/
    #real path=/
    #query=
    #request_version=HTTP/1.1
    #
    #SERVER VALUES:
    #server_version=BaseHTTP/0.3
    #sys_version=Python/2.6.4
    #protocol_version=HTTP/1.0
