#!/usr/bin/env python

import unittest

from aws_saml_auth import configuration


class TestConfigurationMethods(unittest.TestCase):
    def test_config_profile(self):
        self.assertEqual(
            configuration.Configuration.config_profile("default"), "default"
        )
        self.assertEqual(
            configuration.Configuration.config_profile("DEFAULT"), "DEFAULT"
        )
        self.assertEqual(
            configuration.Configuration.config_profile("testing"), "profile testing"
        )
        self.assertEqual(
            configuration.Configuration.config_profile(None), "profile None"
        )
        self.assertEqual(
            configuration.Configuration.config_profile(123456), "profile 123456"
        )

    def test_duration_invalid_values(self):
        # Duration must be an integer
        c = configuration.Configuration()
        c.region = "sample_region"
        c.login_url = "sample_login_url"
        c.duration = "bad_type"
        c.region = "sample_region"
        with self.assertRaises(AssertionError) as e:
            c.raise_if_invalid()
        self.assertIn("Expected duration to be an integer.", str(e.exception))

        # Duration can not be negative
        c = configuration.Configuration()
        c.region = "sample_region"
        c.login_url = "sample_login_url"
        c.duration = -1
        with self.assertRaises(AssertionError) as e:
            c.raise_if_invalid()
        self.assertIn(
            "Expected duration to be greater than or equal to 900.", str(e.exception)
        )

        # Duration can not be greater than MAX_DURATION
        valid = configuration.Configuration()
        valid.login_url = "sample_login_url"
        valid.duration = 900
        c = configuration.Configuration()
        c.region = "sample_region"
        c.login_url = "sample_login_url"
        c.duration = valid.max_duration + 1
        with self.assertRaises(AssertionError) as e:
            c.raise_if_invalid()
        self.assertIn(
            "Expected duration to be less than or equal to max_duration",
            str(e.exception),
        )

    def test_duration_valid_values(self):
        c = configuration.Configuration()
        c.region = "sample_region"
        c.login_url = "sample_login_url"
        c.duration = 900
        self.assertEqual(c.duration, 900)
        c.raise_if_invalid()
        c.duration = c.max_duration
        self.assertEqual(c.duration, c.max_duration)
        c.raise_if_invalid()
        c.duration = c.max_duration - 1
        self.assertEqual(c.duration, c.max_duration - 1)
        c.raise_if_invalid()

    def test_duration_defaults_to_max_duration(self):
        c = configuration.Configuration()
        c.region = "sample_region"
        c.login_url = "sample_login_url"
        self.assertEqual(c.duration, c.max_duration)
        c.raise_if_invalid()

    def test_ask_role_invalid_values(self):
        # ask_role must be a boolean
        c = configuration.Configuration()
        c.region = "sample_region"
        c.login_url = "sample_login_url"
        c.ask_role = "bad_value"
        with self.assertRaises(AssertionError) as e:
            c.raise_if_invalid()
        self.assertIn("Expected ask_role to be a boolean.", str(e.exception))

    def test_ask_role_valid_values(self):
        c = configuration.Configuration()
        c.region = "sample_region"
        c.login_url = "sample_login_url"
        c.ask_role = True
        self.assertTrue(c.ask_role)
        c.raise_if_invalid()
        c = configuration.Configuration()
        c.region = "sample_region"
        c.login_url = "sample_login_url"
        c.ask_role = False
        self.assertFalse(c.ask_role)
        c.raise_if_invalid()

    def test_ask_role_optional(self):
        c = configuration.Configuration()
        c.region = "sample_region"
        c.login_url = "samlple_login_url"
        self.assertTrue(c.ask_role)
        c.raise_if_invalid()

    def test_login_url_invalid_values(self):
        # sp_id must not be None
        c = configuration.Configuration()
        c.region = "sample_region"
        with self.assertRaises(AssertionError) as e:
            c.raise_if_invalid()
        self.assertIn(
            "Expected login_url to be set to non-None value.", str(e.exception)
        )

    def test_profile_defaults_to_sts(self):
        c = configuration.Configuration()
        c.region = "sample_region"
        c.login_url = "sample_login_url"
        self.assertEqual(c.profile, "default")
        c.raise_if_invalid()

    def test_profile_invalid_values(self):
        # profile must be a string
        c = configuration.Configuration()
        c.region = "sample_region"
        c.login_url = "sample_login_url"
        c.profile = 123456
        with self.assertRaises(AssertionError) as e:
            c.raise_if_invalid()
        self.assertIn("Expected profile to be a string.", str(e.exception))

    def test_profile_valid_values(self):
        c = configuration.Configuration()
        c.region = "sample_region"
        c.login_url = "sample_login_url"
        c.profile = "default"
        self.assertEqual(c.profile, "default")
        c.raise_if_invalid()
        c.profile = "sts"
        self.assertEqual(c.profile, "sts")
        c.raise_if_invalid()

    def test_profile_defaults(self):
        c = configuration.Configuration()
        c.region = "sample_region"
        c.login_url = "sample_login_url"
        self.assertEqual(c.profile, "default")
        c.raise_if_invalid()

    def test_region_invalid_values(self):
        # region must be a string
        c = configuration.Configuration()
        c.login_url = "sample_login_url"
        c.region = 1234
        with self.assertRaises(AssertionError) as e:
            c.raise_if_invalid()
        self.assertIn("Expected region to be a string.", str(e.exception))

    def test_region_valid_values(self):
        c = configuration.Configuration()
        c.login_url = "sample_login_url"
        c.region = "us-east-1"
        self.assertEqual(c.region, "us-east-1")
        c.raise_if_invalid()
        c.region = "us-west-2"
        self.assertEqual(c.region, "us-west-2")
        c.raise_if_invalid()

    def test_region_defaults_to_none(self):
        c = configuration.Configuration()
        c.login_url = "sample_login_url"
        self.assertEqual(c.region, None)
        with self.assertRaises(AssertionError) as e:
            c.raise_if_invalid()
        self.assertIn("Expected region to be a string.", str(e.exception))

    def test_role_arn_invalid_values(self):
        # role_arn must be a string
        c = configuration.Configuration()
        c.region = "sample_region"
        c.login_url = "sample_login_url"
        c.role_arn = 1234
        with self.assertRaises(AssertionError) as e:
            c.raise_if_invalid()
        self.assertIn("Expected role_arn to be None or a string.", str(e.exception))

        # role_arn be a arn-looking string
        c = configuration.Configuration()
        c.region = "sample_region"
        c.login_url = "sample_login_url"
        c.role_arn = "bad_string"
        with self.assertRaises(AssertionError) as e:
            c.raise_if_invalid()
        self.assertIn("Expected role_arn to contain 'arn:aws:iam::'", str(e.exception))

    def test_role_arn_is_optional(self):
        c = configuration.Configuration()
        c.region = "sample_region"
        c.login_url = "sample_login_url"
        self.assertIsNone(c.role_arn)
        c.raise_if_invalid()

    def test_role_arn_valid_values(self):
        c = configuration.Configuration()
        c.region = "sample_region"
        c.login_url = "sample_login_url"
        c.role_arn = "arn:aws:iam::some_arn_1"
        self.assertEqual(c.role_arn, "arn:aws:iam::some_arn_1")
        c.raise_if_invalid()
        c.role_arn = "arn:aws:iam::some_other_arn_2"
        self.assertEqual(c.role_arn, "arn:aws:iam::some_other_arn_2")
        c.raise_if_invalid()
