# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

`aws-saml-auth` is a CLI that obtains temporary AWS STS credentials via a SAML IdP (typically Google Workspace).
Unlike its ancestor `aws-google-auth`, it never handles user passwords — it opens the browser and captures the
`SAMLResponse` posted back to a local HTTP server.

## Commands

The project uses `uv`; `pyproject.toml` and `uv.lock` are the source of truth for dependencies.

```shell
uv sync                                 # create .venv and install everything, including dev deps
uv run aws-saml-auth --help             # run the CLI from the checkout

uv run pytest                           # run all tests
uv run pytest aws_saml_auth/tests/test_amazon.py                          # one file
uv run pytest aws_saml_auth/tests/test_amazon.py::TestAmazon::test_sts_client  # one test

uv run ruff format                      # format (CI runs `ruff format --check --diff`)
uv run ruff check                       # lint
uv build                                # build sdist + wheel
```

A direnv `.envrc` running `uv sync` is a convenient setup, but it is not in the repo (it is gitignored globally).

Supported Python is 3.12+; CI runs the tests on 3.12, 3.13 and 3.14. Ruff's default rule set is broad and is
used as-is, with only `BLE001` ignored in `pyproject.toml`.

The version lives in `aws_saml_auth/VERSION`, read at runtime by `__init__.py` and at build time by hatchling.
It is only authoritative at release time: the release and Docker workflows overwrite that file from the pushed
`v*` git tag. Releases to PyPI (`uv publish`) and Docker Hub are tag-triggered.

## Architecture

The flow, orchestrated by `cli()` → `resolve_config()` → `process_auth()` in `aws_saml_auth/__init__.py`:

1. **`configuration.Configuration`** holds every setting and owns all disk I/O against `~/.aws/config` and
   `~/.aws/credentials` (both written under `filelock`). Settings persist into the AWS config file under
   `asa.`-prefixed keys (`asa.login_url`, `asa.role_arn`, `asa.duration`, `asa.ask_role`), so a second run of the
   same profile needs no arguments.
2. **`saml.Saml`** prints and opens `login_url`, then waits for the assertion on two paths at once, whichever
   arrives first: `login_server.LoginServer` (an `HTTPServer` on **port 4589**, `login_server.PORT`) and, when
   interactive, a paste prompt. Both feed one `queue.Queue`; the server thread keeps serving until the main
   thread has an assertion, so stray requests (favicon, prefetch, the user opening the url) cannot end the wait.
3. **`amazon.Amazon`** parses role/principal pairs out of the SAML XML with lxml, calls
   `sts:AssumeRoleWithSAML`, and renders output (`--print-creds`, `--credential-process`, or profile write).
4. **`util.Util`** holds the interactive role picker, `coalesce`, and POST parsing.

### Things that are easy to get wrong

- **Option precedence** is uniformly ARGS → ENV_VAR → config-file/default, implemented with `Util.coalesce` in
  `resolve_config`. Boolean "negative" flags (`--no-ask-role`, `--no-saml-cache`, `--no-resolve-aliases`) invert
  this: their env var (`ASA_NO_ASK_ROLE` etc.) is checked *first* and only for presence, not value.
- **Two independent caches.** The SAML assertion cache is a file next to the credentials file named by a SHA1 of
  the login URL, and is validated against the assertion's `NotBefore`/`NotOnOrAfter`. The token cache lives in the
  credentials file under `asa.`-prefixed keys and is only read in `--credential-process` mode. Both getters return
  `None` when stale, so callers can treat "expired" and "absent" identically. With a valid token cache `saml_xml`
  is `None` and the role-selection block is skipped entirely.
- **`--credential-process` forces `quiet` and `ask_role=False`** — it must emit only the JSON document the AWS CLI
  expects on stdout.
- **`Amazon.sts_client` deliberately unsets `AWS_PROFILE`** around client construction, so the STS call that
  obtains credentials isn't made using the profile being written to.
- **`--auto-duration`** requests `max_duration` (43200) and, on the STS `ValidationError`, regex-parses the
  allowed maximum out of the error message and retries once.
- **Two servers, two roles.** `login_server` runs locally to receive the assertion. `redirect_server`
  (`--redirect-server`, `$PORT`) is meant to be deployed publicly (e.g. Cloud Run) as the SAML `ACS URL` and
  redirects the POST to the login server; that deployment also requires `SAML:aud` on the IAM role's
  trust policy to include the redirect server's URL.
- `Util.parse_post` only accepts `application/x-www-form-urlencoded`, which is what the SAML HTTP-POST binding
  sends; anything else yields an empty dict. It and `parse_query` return flat dicts, not `parse_qs` lists.
- **Only the credentials document goes to stdout.** Prompts, the role table, errors and progress all go to
  stderr via `Util.echo`/`Util.get_input`, because `--credential-process` output is parsed as JSON.
- **`cli()` must exit non-zero on failure.** botocore only surfaces a credential process's stderr when it exits
  non-zero; on exit 0 it parses stdout and reports `Expecting value: line 1 column 1 (char 0)` instead of the
  real error.
- **The redirect server 303s with the assertion in the query string** (`redirect_server` → `login_server.URL`),
  not a 307 replaying the POST, so the assertion survives in the address bar for the paste fallback. HTTPS pages
  cannot `fetch`/iframe `http://127.0.0.1` (mixed content), so a top-level redirect is the only option. Clients
  before 0.9.0 have no `do_GET` and break against a newer redirect server.
- **With `ask_role` false the role must be unambiguous**: `resolve_role` errors listing the available roles
  rather than falling through to the interactive picker, which can never work under `--credential-process`.
- Both `arn:aws:iam:` and `arn:aws-us-gov:iam:` ARNs are accepted in role parsing and validation — keep both
  branches in sync.

Documentation is `README.rst` (reStructuredText, lint-checked with `rst-lint`); it is also the PyPI long
description.
