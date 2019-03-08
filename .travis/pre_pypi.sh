#!/bin/sh -e

. .travis/_include.sh
set -x

if [ -e "$DIST_PATH" ]; then
    mv "$DIST_PATH" "${DIST_PATH}_old"
    mkdir -p "$DIST_PATH"
    mv "${DIST_PATH}_old/"*.whl "${DIST_PATH}_old/"*.tar.gz "$DIST_PATH" || true
    rm -r "${DIST_PATH}_old"
fi
