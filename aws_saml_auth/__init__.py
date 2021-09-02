#!/usr/bin/env python
from __future__ import print_function

import argparse
import base64
import os
import sys
import logging

from six import print_ as print
from tzlocal import get_localzone

from aws_saml_auth import amazon
from aws_saml_auth import configuration
from aws_saml_auth import saml
from aws_saml_auth import util

with open(
    os.path.join(os.path.abspath(os.path.dirname(__file__)), "VERSION"),
    encoding="utf-8",
) as version_file:
    version = version_file.read().strip()


def parse_args(args):
    parser = argparse.ArgumentParser(
        prog="aws-saml-auth",
        description="Acquire temporary AWS credentials via SAML",
    )

    main_group = parser.add_mutually_exclusive_group()
    main_group.add_argument(
        "--redirect-server",
        action="store_true",
        help="Run the redirect server on port ($PORT)",
    )
    main_group.add_argument(
        "-L", "--login-url", help="SAML Provider login url ($ASA_LOGIN_URL)"
    )
    parser.add_argument(
        "-R", "--region", help="AWS region endpoint ($AWS_DEFAULT_REGION)"
    )
    duration_group = parser.add_mutually_exclusive_group()
    duration_group.add_argument(
        "-d",
        "--duration",
        type=int,
        help="Credential duration in seconds (defaults to value of $ASA_DURATION, then falls back to 43200)",
    )
    duration_group.add_argument(
        "--auto-duration",
        action="store_true",
        help="Tries to use the longest allowed duration ($ASA_AUTO_DURATION=1)",
    )
    parser.add_argument(
        "-p",
        "--profile",
        help="AWS profile (defaults to value of $AWS_PROFILE, then falls back to 'default')",
    )
    parser.add_argument(
        "-A", "--account", help="Filter for specific AWS account ($ASA_AWS_ACCOUNT)"
    )
    parser.add_argument("-q", "--quiet", action="store_true", help="Quiet output")
    parser.add_argument(
        "--saml-assertion",
        dest="saml_assertion",
        help="Base64 encoded SAML assertion to use",
    )
    parser.add_argument(
        "--no-saml-cache",
        dest="use_saml_cache",
        action="store_false",
        help="Do not cache the SAML Assertion ($ASA_NO_SAML_CACHE=1)",
    )
    print_group = parser.add_mutually_exclusive_group()
    print_group.add_argument(
        "--print-creds", action="store_true", help="Print Credentials"
    )
    print_group.add_argument(
        "--credential-process",
        action="store_true",
        help="Output suitable for aws cli credential_process ($ASA_CREDENTIAL_PROCESS=1)",
    )
    parser.add_argument(
        "--no-resolve-aliases",
        dest="resolve_aliases",
        action="store_false",
        help="Do not resolve AWS account aliases. ($ASA_NO_RESOLVE_ALIASES=1)",
    )
    parser.add_argument("--port", type=int, help="Port for the redirect server ($PORT)")

    role_group = parser.add_mutually_exclusive_group()
    role_group.add_argument(
        "--no-ask-role",
        dest="ask_role",
        action="store_false",
        help="Never ask to pick the role ($ASA_NO_ASK_ROLE=1)",
    )
    role_group.add_argument(
        "-r", "--role-arn", help="The ARN of the role to assume ($ASA_ROLE_ARN)"
    )
    parser.add_argument(
        "-l",
        "--log",
        dest="log_level",
        choices=["debug", "info", "warn"],
        default="warn",
        help="Select log level (default: %(default)s)",
    )
    parser.add_argument(
        "-V",
        "--version",
        action="version",
        version="%(prog)s {version}".format(version=version),
    )

    return parser.parse_args(args)


def exit_if_unsupported_python():
    if sys.version_info.major == 2 and sys.version_info.minor < 7:
        logging.critical(
            "%s requires Python 2.7 or higher. Please consider "
            "upgrading. Support for Python 2.6 and lower was "
            "dropped because this tool's dependencies dropped "
            "support.",
            __name__,
        )
        logging.critical(
            "For debugging, it appears you're running: %s", sys.version_info
        )
        logging.critical(
            "For more information, see: "
            "https://github.com/cevoaustralia/aws-google-auth/"
            "issues/41"
        )
        sys.exit(1)


def cli(cli_args):
    try:
        exit_if_unsupported_python()

        args = parse_args(args=cli_args)

        # Set up logging
        logging.getLogger().setLevel(getattr(logging, args.log_level.upper(), None))

        config = resolve_config(args)
        if args.redirect_server:
            from aws_saml_auth.redirect_server import start_redirect_server

            start_redirect_server(config.port)
            return

        process_auth(args, config)
    except amazon.ExpectedAmazonException as ex:
        print(ex)
        sys.exit(1)
    except saml.ExpectedSamlException as ex:
        print(ex)
        sys.exit(1)
    except KeyboardInterrupt:
        pass
    except Exception as ex:
        logging.exception(ex)


def resolve_config(args):

    # Shortening Convenience functions
    coalesce = util.Util.coalesce

    # Create a blank configuration object (has the defaults pre-filled)
    config = configuration.Configuration()

    # Have the configuration update itself via the ~/.aws/config on disk.
    # Profile (Option priority = ARGS, ENV_VAR, DEFAULT)
    config.profile = coalesce(args.profile, os.getenv("AWS_PROFILE"), config.profile)

    # Now that we've established the profile, we can read the configuration and
    # fill in all the other variables.
    config.read(config.profile)

    # Ask Role (Option priority = ARGS, ENV_VAR, DEFAULT)
    config.ask_role = coalesce(
        (False if os.getenv("ASA_NO_ASK_ROLE") != None else None),
        args.ask_role,
        config.ask_role,
    )

    # Do not cache the SAML Assertion (Option priority = ARGS, ENV_VAR, DEFAULT)
    config.use_saml_cache = coalesce(
        (False if os.getenv("ASA_NO_SAML_CACHE") != None else None),
        args.use_saml_cache,
        config.use_saml_cache,
    )

    # Duration (Option priority = ARGS, ENV_VAR, DEFAULT)
    config.duration = int(
        coalesce(args.duration, os.getenv("ASA_DURATION"), config.duration)
    )

    # Automatic duration (Option priority = ARGS, ENV_VAR, DEFAULT)
    config.auto_duration = args.auto_duration or os.getenv("ASA_AUTO_DURATION") != None

    # Login URL (Option priority = ARGS, ENV_VAR, DEFAULT)
    config.login_url = coalesce(
        args.login_url, os.getenv("ASA_LOGIN_URL"), config.login_url
    )

    # Region (Option priority = ARGS, ENV_VAR, DEFAULT)
    config.region = coalesce(
        args.region, os.getenv("AWS_DEFAULT_REGION"), config.region
    )

    # ROLE ARN (Option priority = ARGS, ENV_VAR, DEFAULT)
    config.role_arn = coalesce(
        args.role_arn, os.getenv("ASA_ROLE_ARN"), config.role_arn
    )

    # Resolve AWS aliases enabled (Option priority = ARGS, ENV_VAR, DEFAULT)
    config.resolve_aliases = coalesce(
        (False if os.getenv("ASA_NO_RESOLVE_ALIASES") != None else None),
        args.resolve_aliases,
        config.resolve_aliases,
    )

    # Account (Option priority = ARGS, ENV_VAR, DEFAULT)
    config.account = coalesce(
        args.account, os.getenv("ASA_AWS_ACCOUNT"), config.account
    )

    config.print_creds = coalesce(args.print_creds, config.print_creds)

    # Quiet
    config.quiet = coalesce(args.quiet, config.quiet)

    config.port = int(coalesce(args.port, os.getenv("PORT"), config.port))

    config.credential_process = (
        args.credential_process or os.getenv("ASA_CREDENTIAL_PROCESS") != None
    )
    if config.credential_process:
        config.quiet = True
        config.ask_role = False
        config.read_token_cache()

    if config.use_saml_cache:
        config.read_saml_cache()

    return config


def process_auth(args, config):
    if config.region is None:
        config.region = util.Util.get_input("AWS Region: ")
        logging.debug("%s: region is: %s", __name__, config.region)

    if config.login_url is None:
        config.login_url = util.Util.get_input("Login URL: ")
        logging.debug("%s: login url is: %s", __name__, config.login_url)

    # If there is a valid cache and the user opted to use it, use that instead
    # of prompting the user for input (it will also ignroe any set variables
    # such as username or sp_id and idp_id, as those are built into the SAML
    # response). The user does not need to be prompted for a password if the
    # SAML cache is used.
    if args.saml_assertion:
        saml_xml = base64.b64decode(args.saml_assertion)
    elif config.token_cache:
        saml_xml = None
    elif config.saml_cache:
        saml_xml = config.saml_cache
        logging.info("%s: SAML cache found", __name__)
    else:
        saml_client = saml.Saml(config)
        saml_xml = saml_client.do_browser_saml()

    # We now have a new SAML value that can get cached (If the user asked
    # for it to be)
    if config.use_saml_cache:
        config.saml_cache = saml_xml

    # The amazon_client now has the SAML assertion it needed (Either via the
    # cache or freshly generated). From here, we can get the roles and continue
    # the rest of the workflow regardless of cache.
    amazon_client = amazon.Amazon(config, saml_xml)
    if saml_xml is not None:
        roles = amazon_client.roles

        # Determine the provider and the role arn (if the the user provided isn't an option)
        if config.role_arn in roles and not config.ask_role:
            config.provider = roles[config.role_arn]
        else:
            if config.account and config.resolve_aliases:
                aliases = amazon_client.resolve_aws_aliases(roles)
                config.role_arn, config.provider = util.Util.pick_a_role(
                    roles, aliases, config.account
                )
            elif config.account:
                config.role_arn, config.provider = util.Util.pick_a_role(
                    roles, account=config.account
                )
            elif config.resolve_aliases:
                aliases = amazon_client.resolve_aws_aliases(roles)
                config.role_arn, config.provider = util.Util.pick_a_role(roles, aliases)
            else:
                config.role_arn, config.provider = util.Util.pick_a_role(roles)
        if not config.quiet:
            print("Assuming " + config.role_arn)
            print(
                "Credentials Expiration: "
                + format(amazon_client.expiration.astimezone(get_localzone()))
            )

    if config.credential_process:
        amazon_client.print_credential_process()
        config.write_token_cache(amazon_client)
    elif config.print_creds:
        amazon_client.print_export_line()
    elif config.profile:
        config.write(amazon_client)

    config.write_saml_cache()


def main():
    cli_args = sys.argv[1:]
    cli(cli_args)


if __name__ == "__main__":
    main()
