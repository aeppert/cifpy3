import datetime
import http.server
import re
import urllib.parse
import json
import cgi
import copy

import setproctitle

import cif


class Handler(http.server.BaseHTTPRequestHandler):

    def __init__(self, *args):
        self.token = None
        http.server.BaseHTTPRequestHandler.__init__(self, *args)
        
    def connect_to_backend(self):
        try:
            setproctitle.setproctitle('CIF-SERVER (API Handle, {0} {1})'.format(self.command, self.path))
        except:
            pass
        # Based on the startup options for cif-server, let's get the backend + instantiate the class from that module
        self.server.logging.debug("Loading backend: {0}".format(cif.options.storage.lower()))
        self.backend = getattr(__import__("cif.backends.{0}".format(
            cif.options.storage.lower()), fromlist=[cif.options.storage.title()]), cif.options.storage.title()
        )()

        # Connect to the backend
        self.server.logging.debug("Connecting to backend: {0}".format(cif.options.storage_uri))
        self.backend.connect(cif.options.storage_uri)
        self.server.logging.info("Connected to backend: {0}".format(cif.options.storage_uri))

    def check_authentication(self):
        """Checks authentication for an incoming request

        :returns: True on success, False on failure
        :rtype: bool
        """
        self.server.logging.debug("Checking Authentication for {0}:{1}".format(self.client_address[0], self.client_address[1]))
        # If Authentication was disabled via the command line bypass the auth checks
        if "noauth" in cif.options and cif.options.noauth:
            self.server.logging.debug("Noauth is enabled. Returning TRUE for for {0}:{1}".format(self.client_address[0], self.client_address[1]))
            return True

        if "Authorization" not in self.headers:
            self.server.logging.debug("No Authorization header sent for {0}:{1}".format(self.client_address[0], self.client_address[1]))
            self.send_error(401, 'Not Authorized', 'No Token sent. It must be sent using the Authorization header.')
            return False

        if self.token is None:
            self.server.logging.debug("Looking up Token '{0}' for {1}:{2}".format(self.headers['Authorization'], self.client_address[0], self.client_address[1]))
            try:
                self.token = self.backend.token_get(self.headers['Authorization'])
            except LookupError as e:
                self.server.logging.warning("Unauthorized token '{0}' attempting to be used by {1}:{2}".format(self.headers['Authorization'], self.client_address[0], self.client_address[1]))
                self.send_error(401, 'Not Authorized', str(e))
                return False
            except RuntimeError as e:
                self.send_error(500, 'Internal Server Error', str(e))
                self.server.logging.exception('Exception while handling authorization')

        if self.token.revoked:
            self.send_error(401, 'Not Authorized', 'Token has been revoked')
            return False

        # Check token expiration
        if self.token.expires is not None and self.token.expires <= datetime.datetime.utcnow():
            self.server.logging.warning("Expired token '{0}' attempting to be used by {1}:{2}".format(self.headers['Authorization'], self.client_address[0], self.client_address[1]))
            self.send_error(401, 'Not Authorized', 'Token has expired.')
            return False

        return True

    def is_admin(self):
        """Checks Admin status of an Authenticated token.

        :returns: True on success, False on failure
        :rtype: bool
        """
        self.server.logging.debug("Checking admin authentication for {0}:{1}".format(self.client_address[0], self.client_address[1]))
        # If Authentication was disabled via the command line assume everyone is an admin
        if "noauth" in cif.options and cif.options.noauth:
            self.server.logging.debug("Noauth is enabled. Returning admin TRUE for for {0}:{1}".format(self.client_address[0], self.client_address[1]))
            return True

        if not self.token.admin:
            self.server.logging.debug("Non-Admin tried to do something from {0}:{1}".format(self.client_address[0], self.client_address[1]))
            self.send_error(403, 'Forbidden', 'Only admins can do this')
            return False

        # User has passed checks and are an admin, return True
        return True

    def send_bad_request(self, error=""):
        """Sends a bad request error to the client

        """
        self.send_error(400, 'Bad Request', 'Requested Path: "{0}" is not valid for this api.\n{0}'.format(self.path,
                                                                                                           error))
    def do_HEAD(self):
        """Processes GET requests. These will retrieve or search objects. Tokens can only be listed. Observables can be
        searched.

        """
        self.connect_to_backend()
        if not self.check_authentication():
            return

        # Run a regex match against the path for supported methods and queries
        match = re.search(r'^/(?P<object>observables?)/?(?:\?(?P<query_string>.*))?$', self.path)

        if match is None:
            self.send_bad_request()
            return

        request = match.groupdict()

        if request['object'] == "observables" and request['query_string'] is not None:
            self.server.logging.debug("Observable search requested by '{0}:{1}' with query_string: '{2}'".format(self.client_address[0], self.client_address[1], request['query_string']))
            # Parses an available query string into a dict
            args = dict(
                (k, v if len(v) > 1 else v[0]) for k, v in urllib.parse.parse_qs(request['query_string']).items()
            )

            if "noauth" not in cif.options or not cif.options.noauth:
                if "group" in args:
                    if not isinstance(args["group"], list):
                        args["group"] = [args["group"]]
                    for idx, group in enumerate(args["group"]):
                        if group not in self.token.groups:
                            del group[idx]
                    if len(args["group"]) == 0:
                        args["group"] = self.token.groups
                else:
                    args["group"] = self.token.groups

            try:
                self.server.logging.debug("Searching backend for query for {0}:{1}".format(self.client_address[0], self.client_address[1]))
                count = self.backend.observable_search(args, count_only=True)
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Length', count)
                self.end_headers()
            except LookupError as e:
                self.server.logging.exception('404 Not Found')
                self.send_error(404, 'Not Found', str(e))
            except Exception as e:
                self.server.logging.exception('500 Internal Server Error')
                self.send_error(500, 'Internal Server Error', str(e))
        else:
            self.send_bad_request()
        return
    
    def do_GET(self):
        """Processes GET requests. These will retrieve or search objects. Tokens can only be listed. Observables can be
        searched.

        """
        self.connect_to_backend()
        if not self.check_authentication():
            return

        # Run a regex match against the path for supported methods and queries
        match = re.search(r'^/(?P<object>observables?|tokens?)/?(?:\?(?P<query_string>.*))?$', self.path)

        if match is None:
            self.send_bad_request()
            return

        request = match.groupdict()

        if request['object'] == "observables" and request['query_string'] is not None:
            self.server.logging.debug("Observable search requested by '{0}:{1}' with query_string: '{2}'".format(self.client_address[0], self.client_address[1], request['query_string']))
            # Parses an available query string into a dict
            args = dict(
                (k, v if len(v) > 1 else v[0]) for k, v in urllib.parse.parse_qs(request['query_string']).items()
            )

            if "noauth" not in cif.options or not cif.options.noauth:
                if "group" in args:
                    if not isinstance(args["group"], list):
                        args["group"] = [args["group"]]
                    for idx, group in enumerate(args["group"]):
                        if group not in self.token.groups:
                            del group[idx]
                    if len(args["group"]) == 0:
                        args["group"] = self.token.groups
                else:
                    args["group"] = self.token.groups

            start = 0
            count = 1000

            if "start" in args:
                if isinstance(args["start"], list):
                    start = int(args["start"][-1])
                else:
                    start = int(args["start"])
                del args['start']

            if "count" in args:
                if isinstance(args["count"], list):
                    count = int(args["count"][-1])
                else:
                    count = int(args["count"])
                del args['count']

            try:
                self.server.logging.debug("Searching backend for query for {0}:{1}".format(self.client_address[0], self.client_address[1]))
                observables = self.backend.observable_search(args, start, count)
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(bytes('[', 'ISO8859-1'))
                for observable in observables[:-1]:
                    self.wfile.write(bytes(json.dumps(observable.todict()) + ", ", 'ISO8859-1'))
                else:
                    self.wfile.write(bytes(json.dumps(observables[-1].todict()), 'ISO8859-1'))
                self.wfile.write(bytes(']', 'ISO8859-1'))
            except LookupError as e:
                self.server.logging.exception("404 Not Found")
                self.send_error(404, 'Not Found', str(e))
            except Exception as e:
                self.server.logging.exception("500 Internal Server Error")
                self.send_error(500, 'Internal Server Error', str(e))
                self.server.logging.exception('Exception while GET')

        elif request['object'] == "tokens":
            if not self.is_admin():
                return
            tokens = self.backend.token_list()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(bytes('[', 'ISO8859-1'))
            for token in tokens[:-1]:
                self.wfile.write(bytes(json.dumps(token.todict()) + ",", 'ISO8859-1'))
            else:
                self.wfile.write(bytes(json.dumps(tokens[-1].todict()), 'ISO8859-1'))
            self.wfile.write(bytes(']', 'ISO8859-1'))
        else:
            self.send_bad_request()
        return

    def do_POST(self):
        """Processes POST requests. POST requests will update an existing object.
        Only tokens can be updated. Returns a 404 if the object isn't found.
        """
        self.connect_to_backend()
        if not self.check_authentication():
            return
        if not self.is_admin():
            return
        match = re.search('^/(?P<object>token)/(?P<id>[a-fA-F0-9]{64})$', self.path)
        if match is None:
            self.send_bad_request()
            return
        # Update the ID with the given post parameters
        content_type, parameter_dict = cgi.parse_header(self.headers.getheader('Content-Type'))
        if content_type == 'multipart/form-data':
            post_variables = cgi.parse_multipart(self.rfile, parameter_dict)
        elif content_type == 'application/x-www-form-urlencoded':
            length = int(self.headers.getheader('content-length'))
            post_variables = urllib.parse.parse_qs(self.rfile.read(length), keep_blank_values=1)
        else:
            post_variables = {}

        request = match.groupdict()

        try:
            token = self.backend.token_get(request['id'])
        except LookupError as e:
            self.send_error(404, 'Not Found', str(e))
            return

        for name, value in post_variables:
            try:
                setattr(token, name, value)
            except Exception as e:
                self.send_error(400, 'Bad Request', str(e))
                return

        try:
            self.backend.token_update(token)
        except Exception as e:
            self.send_error(500, 'Internal Server Error', str(e))
            return



    def do_PUT(self):
        """Processes PUT request. PUT requests will create a new object.
        Sends a 201 (Created) for creating tokens.
        Sends a 202 (Accepted) for creating observables

        """
        self.connect_to_backend()
        if not self.check_authentication:
            return

        match = re.search(r'^/(?P<object>observable?|token?)/?$', self.path)

        if match is None:
            self.send_bad_request()
            return

        # Update the ID with the given post parameters
        content_type, parameter_dict = cgi.parse_header(self.headers['Content-Type'])
        if content_type == 'multipart/form-data':
            post_variables = cgi.parse_multipart(self.rfile, parameter_dict)
        elif content_type == 'application/x-www-form-urlencoded':
            length = int(self.headers['content-length'])
            post_variables = dict((k, v if len(v) > 1 else v[0]) for k, v in urllib.parse.parse_qs(self.rfile.read(length).decode('UTF-8'), keep_blank_values=1).items())
        else:
            post_variables = {}

        request = match.groupdict()

        if request['object'] == "token":
            if not self.is_admin():
                return
            try:
                if "token" in post_variables:
                    del post_variables["token"]
                token = cif.types.Token(post_variables)
                self.backend.token_create(token)
            except Exception as e:
                self.send_error(422, 'Could not process token: {0}'.format(e))
                return
            self.send_response(201)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Location', '/token/{0}'.format(token.token))
            self.end_headers()
            self.wfile.write(bytes(json.dumps(token.todict()), 'ISO8859-1'))

        elif request['object'] == "observable":
            if "observable" not in post_variables:
                self.send_error(422, 'The observable parameter is required')
                return
            try:
                if "id" in post_variables:
                    del post_variables["id"]
                observable = cif.types.Observable(post_variables)
            except Exception as e:
                self.send_error(422, 'Could not process observable: {0}'.format(e))
                return
            self.server.logging.debug("Put {0} into global queue: {1}".format(repr(observable), repr(cif.worker.tasks)))
            cif.worker.tasks.put(observable)
            cif.worker.tasks.close()
            cif.worker.tasks.join_thread()
            self.send_response(202)
            self.send_header('Location', '/observable/{0}'.format(observable.id))
            self.end_headers()
            self.wfile.write(bytes(json.dumps(observable.todict()), 'ISO8859-1'))

    def do_DELETE(self):
        """Handles a DELETE HTTP request. Only tokens can be deleted at this time.
        :return:
        """
        self.connect_to_backend()
        if not self.is_admin():
            return

        match = re.search('^/(?P<object>token)/(?P<id>[a-fA-F0-9]{64})$', self.path)

        if match is None:
            self.send_error(404, 'Not Found')
            return

        request = match.groupdict()

        try:
            self.backend.token_delete(request['id'])
        except Exception as e:
            self.send_error(500, "Failed to delete token: {0}".format(e))
