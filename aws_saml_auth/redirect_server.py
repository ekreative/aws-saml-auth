"""
This HTTP server can be run on a server, and redirects the SAMLResponse to 127.0.0.1 so the command can capture it
"""

import logging
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlencode

from aws_saml_auth import login_server, util

logger = logging.getLogger(__name__)


class RedirectServerHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        assertion = util.Util.parse_post(self).get("SAMLResponse")
        if assertion is None:
            self.send_error(400, "No SAMLResponse in this request")
            return

        # A 303 to a url carrying the assertion, rather than a 307 that
        # repeats the post, so the assertion stays in the address bar. That is
        # the only copy the user can reach when the browser is on a different
        # machine to the command and cannot open 127.0.0.1.
        self.send_response(303)
        self.send_header(
            "location", login_server.URL + "?" + urlencode({"SAMLResponse": assertion})
        )
        self.end_headers()

    def log_message(self, format, *args):
        logger.info("redirect server: " + format, *args)


def start_redirect_server(port):
    logging.basicConfig(level=logging.INFO)
    server_address = ("", port)
    httpd = HTTPServer(server_address, RedirectServerHandler)
    logger.info("Starting http redirect server on: %s", port)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()
    logger.info("Stopping http redirect server")
