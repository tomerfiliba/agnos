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
import time
import errno
import threading
import itertools
import signal
from optparse import OptionParser
from .transports import SocketTransportFactory
from .utils import Logger, LogSink, NullLogger


def _handle_client(processor, logger):
    logger.info("handling %s", processor.transport)
    try:
        while True:
            processor.process()
    except EOFError:
        logger.info("got EOF")
    except KeyboardInterrupt:
        logger.info("got SIGINT")
        raise
    except Exception:
        logger.exception()
        raise
    finally:
        logger.info("client handler quits")
        processor.transport.close()

class BaseServer(object):
    def __init__(self, processor_factory, transport_factory, logger):
        self.processor_factory = processor_factory
        self.transport_factory = transport_factory
        self.logger = logger
        self.logger.info("server details: %s, pid = %d", self, os.getpid())
    
    def __del__(self):
        self.close()
    
    def close(self):
        self.logger.info("server is shutting down")
        self.transport_factory.close()
    
    def serve(self):
        self.logger.info("started serving")
        while True:
            try:
                trans = self.transport_factory.accept()
            except IOError, ex:
                if ex.errno == errno.EINTR:
                    continue
                else:
                    raise
            self.logger.info("accepted %s", trans)
            processor = self.processor_factory(trans)
            self._serve_client(processor)
        
    def _serve_client(self, processor):
        raise NotImplementedError()

class SimpleServer(BaseServer):
    def __init__(self, processor_factory, transport_factory, logger = NullLogger):
        BaseServer.__init__(self, processor_factory, transport_factory, logger.sublogger("srv"))
    
    def _serve_client(self, processor):
        self._handle_client(processor, self.logger)

class ThreadedServer(BaseServer):
    def __init__(self, processor_factory, transport_factory, logger = NullLogger):
        BaseServer.__init__(self, processor_factory, transport_factory, logger.sublogger("srv"))
        self._thread_ids = itertools.count(0)

    def _serve_client(self, processor):
        logger2 = self.logger.sublogger("thread%04d" % (self._thread_ids.next(),))
        t = threading.Thread(target = _handle_client, args = (processor, logger2))
        t.start()

class ForkingServer(BaseServer):
    def __init__(self, processor_factory, transport_factory, logger):
        BaseServer.__init__(self, processor_factory, transport_factory, 
            logger.sublogger("srv"))
        self.child_processes = set()
        self._prev_handler = signal.SIG_DFL
        self._closed = True
    
    def _sigchld_handler(self, signum, unused):
        try:
            while True:
                pid, dummy = os.waitpid(-1, os.WNOHANG)
                if pid <= 0:
                    break
                self.logger.info("collected %s", pid)
                self.child_processes.discard(pid)
        except OSError:
            pass
        # re-register signal handler (see man signal(2), under Portability)
        signal.signal(signal.SIGCHLD, self._sigchld_handler)

    def serve(self):
        self._prev_handler = signal.signal(signal.SIGCHLD, self._sigchld_handler)
        self._closed = False
        BaseServer.serve(self)

    def close(self, grace_period = 2):
        if self._closed:
            return
        self._closed = True
        signal.signal(signal.SIGCHLD, self._prev_handler)
        children = set(self.child_processes)
        self.child_processes.clear()
        
        BaseServer.close(self)
        for pid in children:
            try:
                self.logger.info("sending SIGINT to %s", pid)
                os.kill(pid, signal.SIGINT)
            except OSError:
                pass
        if children:
            time.sleep(grace_period)
        for pid in children:
            try:
                self.logger.info("sending SIGKILL to %s", pid)
                os.kill(pid, signal.SIGKILL)
            except OSError:
                pass
    
    def _serve_client(self, processor):
        pid = os.fork()
        if pid == 0:
            # child
            try:
                self.logger = self.logger.sublogger("%d" % (os.getpid(),))
                self._closed = True
                self.logger.info("child proc started")
                signal.signal(signal.SIGCHLD, signal.SIG_DFL)
                _handle_client(processor, self.logger)
            except Exception, ex:
                logger.exception()
            finally:
                sys.exit()
            os._exit(1)
        else:
            # parent
            processor.transport.close()
            self.child_processes.add(pid)
            self.logger.info("spawned %d", pid)
    

class LibraryModeServer(BaseServer):
    def serve(self):
        sys.stdout.write("AGNOS\n%s\n%d\n\n" % (self.transport_factory.host, self.transport_factory.port))
        sys.stdout.flush()
        sys.stdout.close()
        trans = self.transport_factory.accept()
        self.transport_factory.close()
        processor = self.processor_factory(trans)
        _handle_client(processor, self.logger)


def server_main(processor_factory, mode = "simple", port = 0, host = "localhost", 
        logfile = ".server.log"):
    parser = OptionParser(conflict_handler="resolve")
    parser.add_option("-m", "--mode", dest="mode", default=mode,
                      help="server mode (simple, threaded, forking, library)",  
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

    if options.logfile:
        logger = Logger(LogSink([open(options.logfile, "w")]))
    elif logfile:
        logger = Logger(LogSink([open(logfile, "w")]))
    else:
        logger = NullLogger

    transport_factory = SocketTransportFactory(int(options.port), options.host)
    if options.mode == "lib" or options.mode == "library":
        s = LibraryModeServer(processor_factory, transport_factory, logger)
    elif options.mode == "simple":
        if int(options.port) == 0:
            parser.error("must specify port for simple mode")
        s = SimpleServer(processor_factory, transport_factory, logger)
    elif options.mode == "threaded":
        if int(options.port) == 0:
            parser.error("must specify port for threaded mode")
        s = ThreadedServer(processor_factory, transport_factory, logger)
    elif options.mode == "forking":
        if int(options.port) == 0:
            parser.error("must specify port for forking mode")
        s = ForkingServer(processor_factory, transport_factory, logger)
    else:
        parser.error("invalid mode: %r" % (options.mode,))
    try:
        s.serve()
    except KeyboardInterrupt:
        pass
    finally:
        s.close()




