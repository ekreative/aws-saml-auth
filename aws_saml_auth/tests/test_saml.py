import base64
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
        url = "http://127.0.0.1:4589/?SAMLResponse=PHNhbWw%2B"
        self.assertEqual(self.read(url).get_nowait(), url)

    def test_retries_until_something_usable(self):
        assertions = self.read("http://127.0.0.1:4589/", "", "PHNhbWw+")
        self.assertEqual(assertions.get_nowait(), "PHNhbWw+")

    # What a terminal in canonical mode does to a pasted assertion
    def test_retries_on_a_truncated_paste(self):
        whole = base64.b64encode(b"<saml>" * 800).decode()
        assertions = self.read(whole[:4033], whole)
        self.assertEqual(assertions.get_nowait(), whole)

    def test_gives_up_on_eof(self):
        assertions = self.read(EOFError())
        self.assertTrue(assertions.empty())


class TestCanPrompt(unittest.TestCase):
    def can_prompt(self, stdin, stderr):
        with (
            mock.patch("sys.stdin") as mock_stdin,
            mock.patch("sys.stderr") as mock_stderr,
        ):
            mock_stdin.isatty.return_value = stdin
            mock_stderr.isatty.return_value = stderr
            return saml.Saml.can_prompt()

    def test_run_by_hand(self):
        self.assertTrue(self.can_prompt(stdin=True, stderr=True))

    # The aws cli captures both streams, so a prompt would never be seen,
    # whether or not stdin happens to still be a terminal
    def test_output_captured(self):
        self.assertFalse(self.can_prompt(stdin=True, stderr=False))
        self.assertFalse(self.can_prompt(stdin=False, stderr=False))

    def test_no_stdin(self):
        self.assertFalse(self.can_prompt(stdin=False, stderr=True))
