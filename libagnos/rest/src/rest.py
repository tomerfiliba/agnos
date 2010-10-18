import traceback
import sys
import agnos
import urlparse
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer 


class PageNotFound(Exception):
    pass


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urlparse.urlparse(self.path)
        try:
            text = self.get_page(parsed_path.path, parsed_path.query)
        except PageNotFound:
            self.send_response(404)
            text = "<html><head><title>Error</title></head><body><pre>Page Not Found</pre></body></html>"
        except Exception:
            self.send_response(501)
            tb = "".join(traceback.format_exception(*sys.exc_info()))
            text = "<html><head><title>Error</title></head><body><pre>%s</pre></body></html>" % (tb,)
        else:
            self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.send_header("Content-length", len(text))
        self.end_headers()
        self.wfile.write(text)
    
    def get_page(self, url, query):
        if url == "/foo":
            raise PageNotFound
        
        if url == "/bar":
            0/0
        
        message = '\n'.join([
                'CLIENT VALUES:',
                'client_address=%s (%s)' % (self.client_address,
                                            self.address_string()),
                'command=%s' % self.command,
                'path=%s' % self.path,
                'real path=%s' % url,
                'query=%s' % query,
                'request_version=%s' % self.request_version,
                '',
                'SERVER VALUES:',
                'server_version=%s' % self.server_version,
                'sys_version=%s' % self.sys_version,
                'protocol_version=%s' % self.protocol_version,
                '',
                ])
        return message
        


def run(host = "localhost", port = 8081):
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
