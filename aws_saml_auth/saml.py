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
    f"If your browser could not reach {login_server.URL}, paste the url it\n"
    "ended up on (or the assertion from the login page) and press enter:\n"
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

        return self._await_assertion()

    # Waits for the assertion on two paths at once: the browser posting or
    # redirecting to the local server, and the user pasting it. Either wins.
    def _await_assertion(self):
        assertions = queue.Queue()
        httpd = LoginServer(("", login_server.PORT), LoginServerHandler, assertions)
        interactive = self.can_prompt()

        threading.Thread(target=self._serve, args=(httpd,), daemon=True).start()
        if interactive:
            threading.Thread(
                target=self._read_paste, args=(assertions,), daemon=True
            ).start()
        else:
            logger.info("Not interactive, only waiting for the browser")

        # The paste prompt takes the terminal out of canonical mode, so its
        # state is restored here whichever path finishes first
        saved_tty = util.Util.tty_attributes() if interactive else None
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
            util.Util.restore_tty(saved_tty)

        return util.Util.decode_assertion(assertion)

    # A prompt is only worth offering if it can be seen and answered. Run by
    # hand that is the terminal, but when the aws cli runs this as a
    # credential process it captures stderr, so the prompt would never appear.
    @staticmethod
    def can_prompt():
        return sys.stdin.isatty() and sys.stderr.isatty()

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
            try:
                util.Util.decode_assertion(pasted)
            except ValueError as ex:
                util.Util.echo(f"{ex}, try again.")
                continue
            assertions.put(pasted)
            return

    @property
    def login_url(self):
        if self.config.login_url is not None:
            return self.config.login_url

        raise ExpectedSamlException("No saml login url provided")
