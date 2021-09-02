import os
import unittest

import mock
from nose.tools import nottest

from aws_saml_auth import resolve_config, parse_args


class TestProfileProcessing(unittest.TestCase):
    def test_default(self):
        args = parse_args([])
        config = resolve_config(args)
        self.assertEqual("default", config.profile)

    def test_cli_param_supplied(self):
        args = parse_args(["-p", "profile"])
        config = resolve_config(args)
        self.assertEqual("profile", config.profile)

    @mock.patch.dict(os.environ, {"AWS_PROFILE": "mytemp"})
    def test_with_environment(self):
        args = parse_args([])
        config = resolve_config(args)
        self.assertEqual("mytemp", config.profile)

        args = parse_args(["-p", "profile"])
        config = resolve_config(args)
        self.assertEqual("profile", config.profile)


class TestDurationProcessing(unittest.TestCase):
    def test_default(self):
        args = parse_args([])
        config = resolve_config(args)
        self.assertEqual(43200, config.duration)

    def test_cli_param_supplied(self):
        args = parse_args(["-d", "500"])
        config = resolve_config(args)
        self.assertEqual(500, config.duration)

    def test_invalid_cli_param_supplied(self):

        with self.assertRaises(SystemExit):
            args = parse_args(["-d", "blart"])
            resolve_config(args)

    @mock.patch.dict(os.environ, {"ASA_DURATION": "3000"})
    def test_with_environment(self):
        args = parse_args([])
        config = resolve_config(args)
        self.assertEqual(3000, config.duration)

        args = parse_args(["-d", "500"])
        config = resolve_config(args)
        self.assertEqual(500, config.duration)


class TestLoginUrlProcessing(unittest.TestCase):
    @mock.patch.dict(os.environ, {"AWS_PROFILE": "mytemp"})
    def test_default(self):
        args = parse_args([])
        config = resolve_config(args)
        self.assertEqual(None, config.login_url)

    def test_cli_param_supplied(self):
        args = parse_args(["-L", "kjl2342"])
        config = resolve_config(args)
        self.assertEqual("kjl2342", config.login_url)

    @mock.patch.dict(os.environ, {"ASA_LOGIN_URL": "adsfasf233423"})
    def test_with_environment(self):
        args = parse_args([])
        config = resolve_config(args)
        self.assertEqual("adsfasf233423", config.login_url)

        args = parse_args(["-L", "kjl2342"])
        config = resolve_config(args)
        self.assertEqual("kjl2342", config.login_url)


class TestRegionProcessing(unittest.TestCase):
    @nottest
    def test_default(self):
        args = parse_args([])
        config = resolve_config(args)
        self.assertEqual(None, config.region)

    def test_cli_param_supplied(self):
        args = parse_args(["--region", "ap-southeast-4"])
        config = resolve_config(args)
        self.assertEqual("ap-southeast-4", config.region)

    @mock.patch.dict(os.environ, {"AWS_DEFAULT_REGION": "ap-southeast-9"})
    def test_with_environment(self):
        args = parse_args([])
        config = resolve_config(args)
        self.assertEqual("ap-southeast-9", config.region)

        args = parse_args(["--region", "ap-southeast-4"])
        config = resolve_config(args)
        self.assertEqual("ap-southeast-4", config.region)


class TestRoleProcessing(unittest.TestCase):
    @mock.patch.dict(os.environ, {"AWS_PROFILE": "mytemp"})
    def test_default(self):
        args = parse_args([])
        config = resolve_config(args)
        self.assertEqual(None, config.role_arn)

    def test_cli_param_supplied(self):
        args = parse_args(["-r", "role1234"])
        config = resolve_config(args)
        self.assertEqual("role1234", config.role_arn)

    @mock.patch.dict(os.environ, {"ASA_ROLE_ARN": "4567-role"})
    def test_with_environment(self):
        args = parse_args([])
        config = resolve_config(args)
        self.assertEqual("4567-role", config.role_arn)


class TestAskRoleProcessing(unittest.TestCase):
    def test_default(self):
        args = parse_args([])
        config = resolve_config(args)
        self.assertTrue(config.ask_role)

    def test_cli_param_supplied(self):
        args = parse_args(["--no-ask-role"])
        config = resolve_config(args)
        self.assertFalse(config.ask_role)

    @nottest
    @mock.patch.dict(os.environ, {"ASA_ASK_ROLE": "true"})
    def test_with_environment(self):
        args = parse_args([])
        config = resolve_config(args)
        self.assertTrue(config.ask_role)


class TestResolveAliasesProcessing(unittest.TestCase):
    def test_default(self):
        args = parse_args([])
        config = resolve_config(args)
        self.assertTrue(config.resolve_aliases)

    def test_cli_param_supplied(self):
        args = parse_args(["--no-resolve-aliases"])
        config = resolve_config(args)
        self.assertFalse(config.resolve_aliases)

    @nottest
    @mock.patch.dict(os.environ, {"ASA_NO_RESOLVE_AWS_ALIASES": "true"})
    def test_with_environment(self):
        args = parse_args([])
        config = resolve_config(args)
        self.assertFalse(config.resolve_aliases)


class TestAccountProcessing(unittest.TestCase):
    @nottest
    def test_default(self):
        args = parse_args([])
        config = resolve_config(args)
        self.assertEqual(None, config.account)

    def test_cli_param_supplied(self):
        args = parse_args(["--account", "123456789012"])
        config = resolve_config(args)
        self.assertEqual("123456789012", config.account)

    @mock.patch.dict(os.environ, {"ASA_AWS_ACCOUNT": "123456789012"})
    def test_with_environment(self):
        args = parse_args([])
        config = resolve_config(args)
        self.assertEqual("123456789012", config.account)

        args = parse_args(["--region", "123456789012"])
        config = resolve_config(args)
        self.assertEqual("123456789012", config.account)
