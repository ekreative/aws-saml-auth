import threading
import unittest
import urllib.error
import urllib.parse
import urllib.request
from http.server import HTTPServer

from aws_saml_auth import login_server, redirect_server, util


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class TestRedirectServer(unittest.TestCase):
    def setUp(self):
        self.httpd = HTTPServer(("127.0.0.1", 0), redirect_server.RedirectServerHandler)
        self.url = f"http://127.0.0.1:{self.httpd.server_address[1]}/saml"
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.httpd.shutdown()
        self.httpd.server_close()
        self.thread.join(timeout=5)

    # The redirect points at the login server, which is not running here, so
    # the redirect is never followed and comes back as an HTTPError
    def post(self, body):
        request = urllib.request.Request(
            self.url,
            data=body.encode("utf-8"),
            headers={"content-type": "application/x-www-form-urlencoded"},
        )
        try:
            return urllib.request.build_opener(NoRedirect).open(request, timeout=5)
        except urllib.error.HTTPError as e:
            return e

    def test_assertion_ends_up_in_the_location(self):
        response = self.post(urllib.parse.urlencode({"SAMLResponse": "PHNhbWw+foo="}))
        self.assertEqual(response.code, 303)
        location = response.headers["location"]
        self.assertTrue(location.startswith(login_server.URL))
        self.assertEqual(util.Util.extract_saml_response(location), "PHNhbWw+foo=")

    def test_post_without_an_assertion(self):
        self.assertEqual(self.post("RelayState=").code, 400)
