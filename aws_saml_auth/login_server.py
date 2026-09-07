"""
This HTTP server for capturing the SAMLResponse that is redirected to 127.0.0.1
"""

import logging
import queue
from http.server import BaseHTTPRequestHandler, HTTPServer

from aws_saml_auth import util

logger = logging.getLogger(__name__)

PORT = 4589
URL = f"http://127.0.0.1:{PORT}/"

PAGE = """<html>
<head><title>{title}</title></head>
<body>{body}</body>
</html>
"""


class LoginServer(HTTPServer):
    # Requests that are not the assertion (favicon, prefetches, the user
    # opening the url themselves) must not end the wait, so responses are
    # handed over a queue and the server keeps serving until told to stop.
    def __init__(self, server_address, handler_class, assertions=None):
        super().__init__(server_address, handler_class)
        self.assertions = assertions if assertions is not None else queue.Queue()


class LoginServerHandler(BaseHTTPRequestHandler):
    def _respond(self, status, title, body):
        encoded = PAGE.format(title=title, body=body).encode("utf-8")
        self.send_response(status)
        self.send_header("content-type", "text/html; charset=utf-8")
        self.send_header("content-length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def _accept(self, assertion):
        if assertion is None:
            self._respond(
                400,
                "Waiting",
                "No SAMLResponse in this request, still waiting for the login.",
            )
            return
        self.server.assertions.put(assertion)
        self._respond(
            200, "Success", "Check your console<script>window.close()</script>"
        )

    # The redirect server sends the assertion as a query parameter so that it
    # stays visible in the address bar, which is the only way to recover it
    # when the browser cannot reach this server.
    def do_GET(self):
        self._accept(util.Util.parse_query(self.path).get("SAMLResponse"))

    def do_POST(self):
        self._accept(util.Util.parse_post(self).get("SAMLResponse"))

    def log_message(self, format, *args):
        logger.debug("login server: " + format, *args)
