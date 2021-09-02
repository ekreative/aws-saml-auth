#!/usr/bin/env python

import unittest

from aws_saml_auth import parse_args


class TestPythonFailOnVersion(unittest.TestCase):
    def test_no_arguments(self):
        """
        This test case exists to validate the default settings of the args parser.
        Changes that break these checks should be considered for backwards compatibility review.
        :return:
        """
        parser = parse_args([])

        self.assertFalse(parser.redirect_server)
        self.assertEqual(parser.login_url, None)
        self.assertTrue(parser.use_saml_cache)
        self.assertEqual(parser.saml_assertion, None)
        self.assertTrue(parser.ask_role)
        self.assertFalse(parser.print_creds)
        self.assertFalse(parser.credential_process)
        self.assertTrue(parser.resolve_aliases)

        self.assertEqual(parser.duration, None)
        self.assertEqual(parser.auto_duration, False)
        self.assertEqual(parser.profile, None)
        self.assertEqual(parser.region, None)
        self.assertEqual(parser.role_arn, None)
        self.assertEqual(parser.quiet, False)
        self.assertEqual(parser.account, None)
        self.assertEqual(parser.port, None)

        # Assert the size of the parameter so that new parameters trigger a review of this function
        # and the appropriate defaults are added here to track backwards compatibility in the future.
        self.assertEqual(len(vars(parser)), 17)

    def test_nocache(self):

        parser = parse_args(["--no-saml-cache"])

        self.assertFalse(parser.use_saml_cache)

    def test_resolvealiases(self):

        parser = parse_args(["--no-resolve-aliases"])

        self.assertFalse(parser.resolve_aliases)

    def test_ask_and_supply_role(self):

        with self.assertRaises(SystemExit):
            parse_args(["-a", "-r", "da-role"])

    def test_invalid_duration(self):
        """
        Should fail parsing a non-int value for `-d`.
        :return:
        """

        with self.assertRaises(SystemExit):
            parse_args(["-d", "abce"])
