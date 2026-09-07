import io
import unittest
from types import SimpleNamespace

from aws_saml_auth import util


class TestUtilMethods(unittest.TestCase):
    def test_coalesce_no_arguments(self):
        self.assertEqual(util.Util.coalesce(), None)

    def test_coalesce_one_argument(self):
        value = "non_none_value"
        self.assertEqual(util.Util.coalesce(value), value)
        self.assertEqual(util.Util.coalesce(None), None)

    def test_coalesce_two_arguments(self):
        value = "non_none_value"
        self.assertEqual(util.Util.coalesce(value, None), value)
        self.assertEqual(util.Util.coalesce(value, value), value)
        self.assertEqual(util.Util.coalesce(None, value), value)
        self.assertEqual(util.Util.coalesce(None, None), None)

    def test_coalesce_many_arguments(self):
        self.assertEqual(
            util.Util.coalesce(None, "test-01", None, "test-02", None, "test-03"),
            "test-01",
        )
        self.assertEqual(
            util.Util.coalesce("test-01", None, "test-02", None, "test-03", None),
            "test-01",
        )
        self.assertEqual(
            util.Util.coalesce(
                None, None, None, None, None, None, None, None, None, None, "test-01"
            ),
            "test-01",
        )


class TestParsePost(unittest.TestCase):
    @staticmethod
    def handler(body, content_type=util.FORM_URLENCODED):
        headers = {"content-length": str(len(body))}
        if content_type is not None:
            headers["content-type"] = content_type
        return SimpleNamespace(headers=headers, rfile=io.BytesIO(body))

    def test_saml_response(self):
        self.assertEqual(
            util.Util.parse_post(self.handler(b"SAMLResponse=abc123&RelayState=")),
            {"SAMLResponse": "abc123", "RelayState": ""},
        )

    def test_content_type_with_charset(self):
        self.assertEqual(
            util.Util.parse_post(
                self.handler(
                    b"SAMLResponse=abc123",
                    content_type="Application/X-WWW-Form-Urlencoded; charset=UTF-8",
                )
            ),
            {"SAMLResponse": "abc123"},
        )

    def test_ignores_other_content_types(self):
        self.assertEqual(
            util.Util.parse_post(self.handler(b"{}", content_type="application/json")),
            {},
        )
        self.assertEqual(util.Util.parse_post(self.handler(b"", content_type=None)), {})


class TestExtractSamlResponse(unittest.TestCase):
    def test_bare_assertion(self):
        self.assertEqual(util.Util.extract_saml_response("PHNhbWw+"), "PHNhbWw+")
        self.assertEqual(util.Util.extract_saml_response("  PHNhbWw+  "), "PHNhbWw+")

    def test_url_copied_from_the_browser(self):
        self.assertEqual(
            util.Util.extract_saml_response(
                "http://127.0.0.1:4589/?SAMLResponse=PHNhbWw%2Bfoo%3D"
            ),
            "PHNhbWw+foo=",
        )

    def test_url_without_an_assertion(self):
        self.assertIsNone(util.Util.extract_saml_response("http://127.0.0.1:4589/"))

    def test_nothing_pasted(self):
        self.assertIsNone(util.Util.extract_saml_response(""))
        self.assertIsNone(util.Util.extract_saml_response("   "))


class TestParseQuery(unittest.TestCase):
    def test_parses_request_path(self):
        self.assertEqual(
            util.Util.parse_query("/?SAMLResponse=abc&RelayState="),
            {"SAMLResponse": "abc", "RelayState": ""},
        )

    def test_no_query(self):
        self.assertEqual(util.Util.parse_query("/"), {})
