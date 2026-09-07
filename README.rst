aws-saml-auth
=============

|github-badge| |pypi-badge|

.. |github-badge| image:: https://github.com/ekreative/aws-saml-auth/workflows/Python%20package/badge.svg
   :target: https://github.com/ekreative/aws-saml-auth/actions
   :alt: GitHub build badge

.. |pypi-badge| image:: https://img.shields.io/pypi/v/aws-saml-auth.svg
   :target: https://pypi.python.org/pypi/aws-saml-auth/
   :alt: PyPI version badge

This command-line tool allows you to acquire AWS temporary (STS)
credentials using Google Workspace as a federated (Single Sign-On, or SSO) provider
or another SAML login provider.


Installation
------------

The easiest option is to to install with ``uv``

.. code:: shell

    uv tool install aws-saml-auth

or with ``pip``

.. code:: shell

    python3 -m pip install aws-saml-auth

Python 3.12 or newer is required.


Its also possible to use the docker image `ekreative/aws-saml-auth`_.

.. _`ekreative/aws-saml-auth`: https://hub.docker.com/r/ekreative/aws-saml-auth


Setup
-----

You will need to know your SAML Providers SSO URL.

For Google Workspace the url by right clicking copy url from the AWS
App that you setup in the Apps menu or from the 'Test SAML Login'
button in the Apps settings.

You can store the url in an env var or pass it to the `--login-url` argument.

.. code:: shell

    export ASA_LOGIN_URL="https://accounts.google.com/o/saml2/initsso?idpid=XXX&spid=XXX&forceauthn=false"


If you dont have an AWS SAML App available talk to your Administrator and point
them to the `Setup AWS SAML and Google Workspace`_ section below.

Credential Process
------------------

In you aws config file (``~/.aws/config``) you can setup a profile to use the credential process

.. code:: ini

    [profile my_profile]
    credential_process = aws-saml-auth --credential-process
    region = eu-west-1
    asa.login_url = https://accounts.google.com/o/saml2/initsso?idpid=some_idp&spid=some_spid&forceauthn=false

If you have multiple roles available you must add the `asa.role_arn` setting. You can also use this to have multiple
profiles with different AWS accounts.

AWS process will trigger the login flow automatically whenever your credentials expire.

Usage
-----

You can run the command ``aws-saml-auth`` to authenticate aws-cli. By default it will edit your default credentials.
You can export the variable ``AWS_PROFILE=my_profile`` and then ``aws-saml-auth`` and aws-cli will use this profile.

.. code:: shell

    $ aws-saml-auth -h
    usage: aws-saml-auth [-h] [--redirect-server | -L LOGIN_URL] [-R REGION] [-d DURATION | --auto-duration] [-p PROFILE] [-A ACCOUNT] [-q] [--saml-assertion SAML_ASSERTION] [--no-saml-cache] [--print-creds | --credential-process]
                     [--no-resolve-aliases] [--port PORT] [--no-ask-role | -r ROLE_ARN] [-l {debug,info,warn}] [-V]

    Acquire temporary AWS credentials via SAML

    optional arguments:
      -h, --help            show this help message and exit
      --redirect-server     Run the redirect server on port ($PORT)
      -L LOGIN_URL, --login-url LOGIN_URL
                            SAML Provider login url ($ASA_LOGIN_URL)
      -R REGION, --region REGION
                            AWS region endpoint ($AWS_DEFAULT_REGION)
      -d DURATION, --duration DURATION
                            Credential duration in seconds (defaults to value of $ASA_DURATION, then falls back to 43200)
      --auto-duration       Tries to use the longest allowed duration ($ASA_AUTO_DURATION=1)
      -p PROFILE, --profile PROFILE
                            AWS profile (defaults to value of $AWS_PROFILE, then falls back to 'default')
      -A ACCOUNT, --account ACCOUNT
                            Filter for specific AWS account ($ASA_AWS_ACCOUNT)
      -q, --quiet           Quiet output
      --saml-assertion SAML_ASSERTION
                            Base64 encoded SAML assertion to use
      --no-saml-cache       Do not cache the SAML Assertion ($ASA_NO_SAML_CACHE=1)
      --print-creds         Print Credentials
      --credential-process  Output suitable for aws cli credential_process ($ASA_CREDENTIAL_PROCESS=1)
      --no-resolve-aliases  Do not resolve AWS account aliases. ($ASA_NO_RESOLVE_ALIASES=1)
      --port PORT           Port for the redirect server ($PORT)
      --no-ask-role         Never ask to pick the role ($ASA_NO_ASK_ROLE=1)
      -r ROLE_ARN, --role-arn ROLE_ARN
                            The ARN of the role to assume ($ASA_ROLE_ARN)
      -l {debug,info,warn}, --log {debug,info,warn}
                            Select log level (default: warn)
      -V, --version         show program's version number and exit


Via Docker
----------

1. Set environment variables for anything listed in Usage with ``($VARIABLE)`` after command line option:

   ``ASA_LOGIN_URL``
   (see above under "Important Data" for how to find these)

   ``AWS_PROFILE``: Optional profile name you want the credentials set for (default is 'sts')

   ``ASA_ROLE_ARN``: Optional ARN of the role to assume

2. For Docker:
   ``docker run -it -e ASA_LOGIN_URL -e AWS_PROFILE -e ASA_ROLE_ARN -p 4589:4589 -v ~/.aws:/root/.aws ekreative/aws-saml-auth``

You will be be shown a URL to visit in your browser

If you have more than one role available to you (and you haven't set up ASA_ROLE_ARN),
you'll be prompted to choose the role from a list.


Logging in without a browser
----------------------------

Inside a container, or over ssh, there is no browser to open and the browser
you do have may not be able to reach ``127.0.0.1:4589`` where the command is
listening. ``aws-saml-auth`` always prints the login url, so open it yourself,
and it waits for the assertion on two paths at once:

* the browser reaching the login server, as usual
* you pasting it, when the browser cannot

After logging in your browser ends up on
``http://127.0.0.1:4589/?SAMLResponse=...``. If that page fails to load, copy
the whole url out of the address bar and paste it at the prompt. Pasting just
the ``SAMLResponse`` value works too.

Publishing the port (``docker run -p 4589:4589 ...``) lets the browser reach
the container directly, and then nothing needs pasting.

The paste prompt needs a terminal, so it is not offered under
``--credential-process``, where the aws cli captures both stdout and stderr and
you would never see it. Log in once directly instead, and the aws cli will use
the cached token afterwards:

.. code:: shell

    aws-saml-auth --credential-process -p my_profile >/dev/null


Storage of profile credentials
------------------------------

Through the use of AWS profiles, using the ``-p`` or ``--profile`` flag, the ``aws-saml-auth`` utility will store the supplied Login Url details in your ``./aws/config`` files.

When re-authenticating using the same profile, the values will be remembered to speed up the re-authentication process.
This enables an approach that enables you to provide your Login URL value only once


Setup AWS SAML and Google Workspace
-----------------------------------

You'll first have to set up your SAML identity provider
(IdP) for AWS. There are tasks to be performed on both the Google Workspace
and the Amazon sides; these references should help you with those
configurations:

-  `How to Set Up Federated Single Sign-On to AWS Using Google
   Apps <https://aws.amazon.com/blogs/security/how-to-set-up-federated-single-sign-on-to-aws-using-google-apps/>`__
-  `Using Google Apps SAML SSO to do one-click login to
   AWS <https://blog.faisalmisle.com/2015/11/using-google-apps-saml-sso-to-do-one-click-login-to-aws/>`__

If you need a fairly simple way to assign users to roles in AWS
accounts, we have another tool called `Google AWS
Federator <https://github.com/cevoaustralia/google-aws-federator>`__
that might help you.

**Note** If you want a longer session than the AWS default 3600 seconds (1 hour)
duration, you must also modify the IAM Role to permit this. See
`the AWS documentation <https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_manage_modify.html>`__
for more information.

To enable browser based login, you will need to host the redirect server
somewhere with HTTPS enabled, you might use a serverless google cloud run deployment for example:

.. code:: shell

    gcloud run deploy --image gcr.io/my-project/aws-saml-auth --args=--redirect-server --platform managed

Beware for google cloud run you must copy the docker image to your account:

.. code:: shell

    docker pull ekreative/aws-saml-auth
    docker tag ekreative/aws-saml-auth gcr.io/my-project/aws-saml-auth
    docker push gcr.io/my-project/aws-saml-auth

Then change your SAML provider settings so the ``ACS URL`` points to the redirect server.

The redirect server answers the ``ACS URL`` post with a 303 to
``http://127.0.0.1:4589/?SAMLResponse=...``, so the assertion stays visible in
the address bar for the paste fallback above. Clients older than 0.9.0 only
accept the assertion as a post, so upgrade them alongside the redirect server.

You will also need to change the Trust Relationship of your IAM Role to allow ``SAML:aud``
to be the host of your redirect server.

See the example, replacing `"https://redirect-server.com/saml"` with your own.

.. code:: json

    {
      "Version": "2012-10-17",
      "Statement": [
        {
          "Effect": "Allow",
          "Principal": {
            "Federated": "arn:aws:iam::XXX:saml-provider/XXX"
          },
          "Action": "sts:AssumeRoleWithSAML",
          "Condition": {
            "StringEquals": {
              "SAML:aud": [
                "https://signin.aws.amazon.com/saml",
                "https://redirect-server.com/saml"
              ]
            }
          }
        }
      ]
    }


Development
-----------

If you want to develop the Aws-saml-auth tool itself, we thank you! The project
uses `uv <https://docs.astral.sh/uv/>`__, which manages the virtualenv and the
locked dependencies for you.

.. code:: shell

    # Create the virtualenv and install everything, including dev dependencies
    uv sync

    # Run the tool from the checkout
    uv run aws-saml-auth --help

    # Run the tests
    uv run pytest

    # Format and lint
    uv run ruff format
    uv run ruff check

If you use `direnv <https://direnv.net/>`__, an ``.envrc`` of

.. code:: shell

    watch_file pyproject.toml uv.lock
    uv sync
    export VIRTUAL_ENV="$PWD/.venv"
    PATH_add "$PWD/.venv/bin"

keeps the environment in sync and on your ``PATH`` when you enter the directory.

We welcome you to review our `code of conduct <CODE_OF_CONDUCT.md>`__ and
`contributing <CONTRIBUTING.md>`__ documents.


Acknowledgments
----------------

This work is inspired by `aws-google-auth <https://github.com/cevoaustralia/aws-google-auth>`__
-- this version has changed to use browser login flow only and avoid handling user passwords.
