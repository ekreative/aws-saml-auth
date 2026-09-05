FROM python:3.14-alpine

COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    PATH="/build/.venv/bin:$PATH"

WORKDIR /build

COPY pyproject.toml uv.lock README.rst ./
COPY aws_saml_auth/ ./aws_saml_auth/

RUN uv sync --locked --no-dev --no-editable

ENTRYPOINT ["aws-saml-auth"]
