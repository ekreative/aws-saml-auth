import unittest
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
