"""
This HTTP server can be run on a server, and hands the SAMLResponse to the
command listening on 127.0.0.1
"""

import html
import logging
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlencode

from aws_saml_auth import login_server, util

logger = logging.getLogger(__name__)

# Browsers may refuse to navigate from this page to a private address, so the
# assertion is in the body as well. Whichever way it fails the user has a copy:
# blocked outright and this page stays up, or navigated and the address bar
# holds the url to paste.
PAGE = """<!doctype html>
<html>
<head><title>aws-saml-auth</title></head>
<body>
<h1>Logged in</h1>
<p><a id="continue" href="{target}">Continue</a></p>
<p>
If nothing happens your browser cannot reach the command. Copy the text below
and paste it at the prompt in your terminal.
</p>
<textarea readonly rows="10" cols="80" onclick="this.select()">{assertion}</textarea>
<script>location.href = document.getElementById("continue").href</script>
</body>
</html>
"""


class RedirectServerHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        assertion = util.Util.parse_post(self).get("SAMLResponse")
        if assertion is None:
            self.send_error(400, "No SAMLResponse in this request")
            return

        target = login_server.URL + "?" + urlencode({"SAMLResponse": assertion})
        body = PAGE.format(
            target=html.escape(target, quote=True), assertion=html.escape(assertion)
        ).encode("utf-8")

        self.send_response(200)
        self.send_header("content-type", "text/html; charset=utf-8")
        self.send_header("content-length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

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
