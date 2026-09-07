import base64
import logging
import queue
import sys
import threading
import webbrowser

from aws_saml_auth import login_server, util
from aws_saml_auth.login_server import LoginServer, LoginServerHandler

logger = logging.getLogger(__name__)

# Long enough for a login that is already under way, short enough that an
# unattended run fails with an error instead of waiting for ever.
UNATTENDED_TIMEOUT = 120

PASTE_PROMPT = (
    f"If your browser could not open {login_server.URL}, paste the url it\n"
    "ended up on (or the SAMLResponse itself) and press enter: "
)


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
        util.Util.echo(f"\nLog in at:\n\n  {self.login_url}\n")
        if not webbrowser.open(self.login_url):
            logger.info("No browser to open, the url above has to be opened by hand")

        return base64.b64decode(self._await_assertion())

    # Waits for the assertion on two paths at once: the browser posting or
    # redirecting to the local server, and the user pasting it. Either wins.
    def _await_assertion(self):
        assertions = queue.Queue()
        httpd = LoginServer(("", login_server.PORT), LoginServerHandler, assertions)
        interactive = sys.stdin.isatty() and not self.config.credential_process

        threading.Thread(target=self._serve, args=(httpd,), daemon=True).start()
        if interactive:
            threading.Thread(
                target=self._read_paste, args=(assertions,), daemon=True
            ).start()
        else:
            logger.info("Not interactive, only waiting for the browser")

        try:
            assertion = assertions.get(
                timeout=None if interactive else UNATTENDED_TIMEOUT
            )
        except queue.Empty:
            raise ExpectedSamlException(
                f"Timed out after {UNATTENDED_TIMEOUT}s waiting for the login "
                f"response on {login_server.URL}. Run `aws-saml-auth -p "
                f"{self.config.profile}` to log in, then try again."
            ) from None
        finally:
            httpd.shutdown()

        return assertion

    @staticmethod
    def _serve(httpd):
        logger.info("Waiting for the login response on %s", login_server.URL)
        with httpd:
            httpd.serve_forever()

    @staticmethod
    def _read_paste(assertions):
        while True:
            try:
                pasted = util.Util.get_input(PASTE_PROMPT)
            except EOFError:
                return
            assertion = util.Util.extract_saml_response(pasted)
            if assertion is not None:
                assertions.put(assertion)
                return
            util.Util.echo("No SAMLResponse found in that, try again.")

    @property
    def login_url(self):
        if self.config.login_url is not None:
            return self.config.login_url

        raise ExpectedSamlException("No saml login url provided")
