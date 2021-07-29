#!/usr/bin/env python

import unittest
from random import randint

import configparser

from aws_saml_auth import configuration


class TestConfigurationPersistence(unittest.TestCase):
    def setUp(self):
        self.c = configuration.Configuration()

        # Pick a profile name that is clear it's for testing. We'll delete it
        # after, but in case something goes wrong we don't want to use
        # something that could clobber user input.
        self.c.profile = "aws_saml_auth_test_{}".format(randint(100, 999))

        self.c.region = "us-east-1"
        self.c.ask_role = False
        self.c.duration = 1234
        self.c.role_arn = "arn:aws:iam::sample_arn"
        self.c.login_url = "sample_login_url"
        self.c.raise_if_invalid()
        self.c.write(None)
        self.c.account = "123456789012"

        self.config_parser = configparser.RawConfigParser()
        self.config_parser.read(self.c.config_file)

    def tearDown(self):
        section_name = configuration.Configuration.config_profile(self.c.profile)
        self.config_parser.remove_section(section_name)
        with open(self.c.config_file, "w") as config_file:
            self.config_parser.write(config_file)

    def test_creating_new_profile(self):
        profile_string = configuration.Configuration.config_profile(self.c.profile)
        self.assertTrue(self.config_parser.has_section(profile_string))
        self.assertEqual(
            self.config_parser[profile_string].get("asa.role_arn"), self.c.role_arn
        )
        self.assertEqual(
            self.config_parser[profile_string].get("asa.login_url"), self.c.login_url
        )
        self.assertEqual(
            self.config_parser[profile_string].get("region"), self.c.region
        )
        self.assertEqual(
            self.config_parser[profile_string].getboolean("asa.ask_role"),
            self.c.ask_role,
        )
        self.assertEqual(
            self.config_parser[profile_string].getint("asa.duration"), self.c.duration
        )

    def test_can_read_all_values(self):
        test_configuration = configuration.Configuration()
        test_configuration.read(self.c.profile)

        test_configuration.raise_if_invalid()

        self.assertEqual(test_configuration.profile, self.c.profile)
        self.assertEqual(test_configuration.role_arn, self.c.role_arn)
        self.assertEqual(test_configuration.login_url, self.c.login_url)
        self.assertEqual(test_configuration.region, self.c.region)
        self.assertEqual(test_configuration.ask_role, self.c.ask_role)
        self.assertEqual(test_configuration.duration, self.c.duration)
