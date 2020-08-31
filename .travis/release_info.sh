#!/bin/sh -e

. .travis/_include.sh
set -x

if [ "$TRAVIS_OS_NAME" = 'linux' ]; then
    env \
        "LINUX_OS=$(lsb_release -sd || echo "unknown linux distro")" \
        "PYTHON=$(python3 -V)" \
        "GLIBC=$(ldd --version | head -n1)" \
    envsubst \
        < RELEASE.tmpl.md > RELEASE.md
fi
