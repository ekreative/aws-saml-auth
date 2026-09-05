import base64
import logging
import webbrowser

from aws_saml_auth.login_server import LoginServer, LoginServerHandler

logger = logging.getLogger(__name__)


class ExpectedSamlException(Exception):
    def __init__(self, *args):
        super().__init__(*args)


class Saml:
    def __init__(self, config):
        """The Saml object opens the browser and catches the redirected response

        login_url: Another providers login url

        These are required to generated the correct login url
        """

        self.config = config

    def do_browser_saml(self):
        logger.warning("Opening url %s", self.login_url)
        webbrowser.open(self.login_url)
        saml_text = self._catch_saml()

        return base64.b64decode(saml_text)

    @staticmethod
    def _catch_saml(port=4589):
        server_address = ("", port)
        httpd = LoginServer(server_address, LoginServerHandler)
        logger.info("Starting http handler...\n")
        httpd.handle_request()

        assert "SAMLResponse" in httpd.post_data, (
            "Expected post data to contain SAMLResponse."
        )
        return httpd.post_data["SAMLResponse"][0]

    @property
    def login_url(self):
        if self.config.login_url is not None:
            return self.config.login_url

        raise ExpectedSamlException("No saml login url provided")
