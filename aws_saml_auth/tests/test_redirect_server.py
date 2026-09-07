import threading
import unittest
import urllib.error
import urllib.parse
import urllib.request
from http.server import HTTPServer

from aws_saml_auth import login_server, redirect_server, util


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

    def post(self, assertion):
        request = urllib.request.Request(
            self.url,
            data=urllib.parse.urlencode({"SAMLResponse": assertion}).encode("utf-8"),
            headers={"content-type": "application/x-www-form-urlencoded"},
        )
        try:
            return urllib.request.urlopen(request, timeout=5)
        except urllib.error.HTTPError as e:
            return e

    def test_page_carries_the_assertion_both_ways(self):
        response = self.post("PHNhbWw+foo=")
        self.assertEqual(response.status, 200)
        page = response.read().decode("utf-8")

        # the link the browser is asked to follow
        target = page.split('href="')[1].split('"')[0]
        self.assertTrue(target.startswith(login_server.URL))
        self.assertEqual(util.Util.extract_saml_response(target), "PHNhbWw+foo=")

        # and a copy to paste when the browser will not follow it
        pasteable = (
            page.split("<textarea", 1)[1].split(">", 1)[1].split("</textarea")[0]
        )
        self.assertEqual(util.Util.extract_saml_response(pasteable), "PHNhbWw+foo=")

    def test_assertion_is_escaped(self):
        page = self.post('a"><script>x</script>').read().decode("utf-8")
        self.assertNotIn("<script>x</script>", page)

    def test_a_realistic_assertion_survives(self):
        assertion = "QUFB" * 2000
        page = self.post(assertion).read().decode("utf-8")
        pasteable = (
            page.split("<textarea", 1)[1].split(">", 1)[1].split("</textarea")[0]
        )
        self.assertEqual(pasteable, assertion)

    def test_post_without_an_assertion(self):
        request = urllib.request.Request(
            self.url,
            data=b"RelayState=",
            headers={"content-type": "application/x-www-form-urlencoded"},
        )
        with self.assertRaises(urllib.error.HTTPError) as e:
            urllib.request.urlopen(request, timeout=5)
        self.assertEqual(e.exception.code, 400)
