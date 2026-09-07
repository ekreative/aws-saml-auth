import queue
import unittest
from unittest import mock

from aws_saml_auth import saml


class TestReadPaste(unittest.TestCase):
    def read(self, *pasted):
        assertions = queue.Queue()
        with (
            mock.patch("aws_saml_auth.util.Util.get_input", side_effect=pasted),
            mock.patch("aws_saml_auth.util.Util.echo"),
        ):
            saml.Saml._read_paste(assertions)
        return assertions

    def test_pasted_assertion(self):
        self.assertEqual(self.read("PHNhbWw+").get_nowait(), "PHNhbWw+")

    def test_pasted_url(self):
        assertions = self.read("http://127.0.0.1:4589/?SAMLResponse=PHNhbWw%2B")
        self.assertEqual(assertions.get_nowait(), "PHNhbWw+")

    def test_retries_until_something_usable(self):
        assertions = self.read("http://127.0.0.1:4589/", "", "PHNhbWw+")
        self.assertEqual(assertions.get_nowait(), "PHNhbWw+")

    def test_gives_up_on_eof(self):
        assertions = self.read(EOFError())
        self.assertTrue(assertions.empty())
