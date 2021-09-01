FROM python:3-alpine

COPY setup.py README.rst /build/
COPY aws_saml_auth/VERSION /build/aws_saml_auth/VERSION

RUN apk add --no-cache libxml2 libxslt musl \
    && apk add --no-cache --virtual .build-deps g++ gcc libxml2-dev libxslt-dev \
    && pip install --no-cache-dir -e /build/ \
    && apk del .build-deps

COPY aws_saml_auth /build/aws_saml_auth

ENTRYPOINT ["aws-saml-auth"]
