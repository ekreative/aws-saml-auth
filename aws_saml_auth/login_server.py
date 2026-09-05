"""
This HTTP server for capturing the SAMLResponse that is redirected to 127.0.0.1
"""

import logging
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import ClassVar

from aws_saml_auth import util

logger = logging.getLogger(__name__)


class LoginServer(HTTPServer):
    post_data: ClassVar[dict] = {}


class LoginServerHandler(BaseHTTPRequestHandler):
    def _set_response(self):
        self.send_response(200)
        self.send_header("content-type", "text/html")
        self.end_headers()
        self.wfile.write(
            b"""
           <html>
           <head><title>Success</title></head>
           <body>
           Check your console
           <script>window.close()</script>
           </body>
           </html>
        """
        )

    def do_POST(self):
        self.server.post_data = util.Util.parse_post(self)
        logger.debug(
            "POST request,\nPath: %s\nHeaders:\n%s\n\nBody:\n%s\n",
            str(self.path),
            str(self.headers),
            self.server.post_data,
        )

        self._set_response()
