import datetime
import http.server
import re
import urllib.parse
import json
import cgi

import cif


class Handler(http.server.BaseHTTPRequestHandler):

    def __init__(self, *args):
        self.token = None
        http.server.BaseHTTPRequestHandler.__init__(self, *args)

    def check_authentication(self):
        """Checks authentication for an incoming request

        :returns: True on success, False on failure
        :rtype: bool
        """

        # If Authentication was disabled via the command line bypass the auth checks
        if "noauth" in cif.options and cif.options.noauth:
            return True

        if "Authorization" not in self.headers:
            self.send_error(401, 'Not Authorized', 'No Token sent. It must be sent using the Authorization header.')
            return False

        if self.token is None:
            try:
                self.token = self.server.backend.token_get(token=self.headers['Authorization'])
            except LookupError as e:
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
            self.send_error(401, 'Not Authorized', 'Token has expired.')
            return False

        return True

    def is_admin(self):
        """Checks Admin status of an Authenticated token.

        :returns: True on success, False on failure
        :rtype: bool
        """

        # If Authentication was disabled via the command line assume everyone is an admin
        if "noauth" in cif.options and cif.options.noauth:
            return True

        if not self.token.admin:
            self.send_error(403, 'Forbidden', 'Only admins can view this')
            return False

        # User has passed checks and are an admin, return True
        return True

    def send_bad_request(self, error=""):
        """Sends a bad request error to the client

        """
        self.send_error(400, 'Bad Request', 'Requested Path: "{0}" is not valid for this api.\n{0}'.format(self.path,
                                                                                                           error))

    def do_GET(self):
        """Processes GET requests. These will retrieve or search objects. Tokens can only be listed. Observables can be
        searched.

        """
        if not self.check_authentication():
            return

        # Run a regex match against the path for supported methods and queries
        match = re.search(r'^/(?P<object>observables?|tokens?)/?(?:\?(?P<query_string>.*))?$', self.path)

        if match is None:
            self.send_bad_request()
            return

        request = match.groupdict()

        if request['object'] == "observables" and request['query_string'] is not None:

                # Parses an available query string into a dict
                args = dict(
                    (k, v if len(v) > 1 else v[0]) for k, v in urllib.parse.parse_qs(request['query_string']).items()
                )

                start = 0
                count = 1000

                if "start" in args:
                    if isinstance(args["start"], list):
                        start = int(args["start"][-1])
                    else:
                        start = int(args["start"])
                    del args['start']

                if "count" in args:
                    if isinstance(args["start"], list):
                        count = int(args["start"][-1])
                    else:
                        count = int(args["count"])
                    del args['count']

                try:

                    observables = self.server.backend.observable_search(args, start, count)
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(bytes('[', 'UTF-8'))
                    for observable in observables[:-1]:
                        self.wfile.write(bytes(json.dumps(observable.todict()) + ", ", 'UTF-8'))
                    else:
                        self.wfile.write(bytes(json.dumps(observables[-1].todict()), 'UTF-8'))
                    self.wfile.write(bytes(']', 'UTF-8'))
                except LookupError as e:
                    self.send_error(404, 'Not Found', str(e))
                except Exception as e:
                    self.send_error(500, 'Internal Server Error', str(e))
                    self.server.logging.exception('Exception while GET')

        elif request['object'] == "tokens":
            if not self.is_admin():
                return
            tokens = self.server.backend.token_list()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(bytes('[', 'UTF-8'))
            for token in tokens[:-1]:
                self.wfile.write(bytes(json.dumps(token.todict()) + ",", 'UTF-8'))
            else:
                self.wfile.write(bytes(json.dumps(tokens[-1].todict()), 'UTF-8'))
            self.wfile.write(bytes(']', 'UTF-8'))
        else:
            self.send_bad_request()
        return

    def do_POST(self):
        """Processes POST requests. POST requests will update an existing object.
        Only tokens can be updated. Returns a 404 if the object isn't found.
        """
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
        print(post_variables)
        # Look up the token first

    def do_PUT(self):
        """Processes PUT request. PUT requests will create a new object.
        Sends a 201 (Created) for creating tokens.
        Sends a 202 (Accepted) for creating observables

        """
        if not self.check_authentication:
            return
        # Put of an object.

        # Check to make sure the object doesn't already exist, if it does send a 409

        # Put the object then return a 201

    def do_DELETE(self):
        """Handles a DELETE HTTP request. Only tokens can be deleted at this time.
        :return:
        """
        if not self.is_admin():
            return
        match = re.search('^/(?P<object>token)/(?P<id>[a-fA-F0-9]{64})$', self.path)
        if match is None:
            self.send_error(404, 'Not Found')
            return
