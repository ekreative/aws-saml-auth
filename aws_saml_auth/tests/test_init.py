import unittest
from typing import ClassVar
from unittest.mock import patch

import aws_saml_auth


class TestInit(unittest.TestCase):
    @patch("aws_saml_auth.cli", spec=True)
    def test_main_method_has_no_parameters(self, mock_cli):
        """
        This is the entrypoint for the cli tool, and should require no parameters

        :param mock_cli:
        :return:
        """

        # Function under test
        aws_saml_auth.main()

        self.assertTrue(mock_cli.called)


class TestResolveRole(unittest.TestCase):
    ROLES: ClassVar[dict] = {
        "arn:aws:iam::123456789012:role/admin": "arn:aws:iam::123456789012:saml-provider/X",
        "arn:aws:iam::123456789012:role/test": "arn:aws:iam::123456789012:saml-provider/X",
    }

    def config(self, role_arn=None):
        config = aws_saml_auth.configuration.Configuration()
        config.role_arn = role_arn
        return config

    def test_role_not_in_the_assertion(self):
        with self.assertRaises(aws_saml_auth.amazon.ExpectedAmazonException) as e:
            aws_saml_auth.resolve_role(
                self.config("arn:aws:iam::999:role/nope"), self.ROLES
            )
        self.assertIn("is not available from this login", str(e.exception))
        self.assertIn("arn:aws:iam::123456789012:role/admin", str(e.exception))

    def test_ambiguous_without_a_role_arn(self):
        with self.assertRaises(aws_saml_auth.amazon.ExpectedAmazonException) as e:
            aws_saml_auth.resolve_role(self.config(), self.ROLES)
        self.assertIn("Set the role to assume", str(e.exception))

    def test_single_role_needs_no_choice(self):
        only = dict([next(iter(self.ROLES.items()))])
        self.assertEqual(
            aws_saml_auth.resolve_role(self.config(), only),
            next(iter(only.items())),
        )
