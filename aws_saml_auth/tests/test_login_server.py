import queue
import threading
import unittest
import urllib.error
import urllib.parse
import urllib.request

from aws_saml_auth import login_server


class TestLoginServer(unittest.TestCase):
    def setUp(self):
        self.assertions = queue.Queue()
        self.httpd = login_server.LoginServer(
            ("127.0.0.1", 0), login_server.LoginServerHandler, self.assertions
        )
        self.url = f"http://127.0.0.1:{self.httpd.server_address[1]}/"
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.httpd.shutdown()
        self.httpd.server_close()
        self.thread.join(timeout=5)

    def post(self, body):
        request = urllib.request.Request(
            self.url,
            data=body.encode("utf-8"),
            headers={"content-type": "application/x-www-form-urlencoded"},
        )
        return urllib.request.urlopen(request, timeout=5)

    def test_assertion_posted(self):
        self.post(urllib.parse.urlencode({"SAMLResponse": "PHNhbWw+"}))
        self.assertEqual(self.assertions.get(timeout=5), "PHNhbWw+")

    def test_assertion_in_query_string(self):
        query = urllib.parse.urlencode({"SAMLResponse": "PHNhbWw+"})
        urllib.request.urlopen(self.url + "?" + query, timeout=5)
        self.assertEqual(self.assertions.get(timeout=5), "PHNhbWw+")

    def test_stray_requests_do_not_end_the_wait(self):
        # A favicon fetch or the user opening the url used to consume the one
        # and only request the server would handle
        with self.assertRaises(urllib.error.HTTPError) as e:
            urllib.request.urlopen(self.url + "favicon.ico", timeout=5)
        self.assertEqual(e.exception.code, 400)

        with self.assertRaises(urllib.error.HTTPError):
            self.post("RelayState=")

        self.assertTrue(self.assertions.empty())

        # and the assertion still arrives afterwards
        self.post(urllib.parse.urlencode({"SAMLResponse": "PHNhbWw+"}))
        self.assertEqual(self.assertions.get(timeout=5), "PHNhbWw+")
