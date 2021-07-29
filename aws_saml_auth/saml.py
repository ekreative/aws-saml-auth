#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function

import base64
import logging
import webbrowser

from aws_saml_auth.login_server import LoginServerHandler, LoginServer


class ExpectedSamlException(Exception):
    def __init__(self, *args):
        super(ExpectedSamlException, self).__init__(*args)


class Saml:
    def __init__(self, config):
        """The Saml object opens the browser and catches the redirected response

        login_url: Another providers login url

        These are required to generated the correct login url
        """

        self.config = config

    def do_browser_saml(self):
        logging.warning("Opening url %s", self.login_url)
        webbrowser.open(self.login_url)
        saml_text = self._catch_saml()

        return base64.b64decode(saml_text)

    @staticmethod
    def _catch_saml(port=4589):
        server_address = ("", port)
        httpd = LoginServer(server_address, LoginServerHandler)
        logging.info("Starting http handler...\n")
        httpd.handle_request()

        assert (
            "SAMLResponse" in httpd.post_data
        ), "Expected post data to contain SAMLResponse."
        return httpd.post_data["SAMLResponse"][0]

    @property
    def login_url(self):
        if self.config.login_url is not None:
            return self.config.login_url

        raise ExpectedSamlException("No saml login url provided")
