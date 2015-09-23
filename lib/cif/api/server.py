__author__ = 'James DeVincentis <james.d@hexhost.net>'

import http.server
import socketserver
import multiprocessing
import sys

import cif


class HTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    def __init__(self, *args, **kwargs):
        http.server.HTTPServer.__init__(self, *args, **kwargs)

        self.logging = cif.logging.getLogger('APIHTTP')

        # Based on the startup options for cif-server, let's get the backend + instantiate the class from that module
        self.logging.debug("Loading backend: {0}".format(cif.options.storage.lower()))
        self.backend = getattr(__import__("cif.backends.{0}".format(
            cif.options.storage.lower()), fromlist=[cif.options.storage.title()]), cif.options.storage.title()
        )()

        # Connect to the backend
        self.logging.debug("Connecting to backend: {0}".format(cif.options.storage_uri))
        self.backend.connect(cif.options.storage_uri)


class Server(multiprocessing.Process):
    def __init__(self):
        multiprocessing.Process.__init__(self)
        self.logging = cif.logging.getLogger('api')
        self.logging.debug("Initialized api Server")

    def run(self):
        self.logging.info("Starting api Server")
        # Run the api server
        server = HTTPServer((cif.options.host, cif.options.port), cif.api.Handler)
        server.serve_forever()
        sys.exit()
