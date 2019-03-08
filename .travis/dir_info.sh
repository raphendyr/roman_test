#!/bin/sh

. .travis/_include.sh

set --
for d in \
    "${PIP_CACHE_DIR:-$HOME/.cache/pip}" \
    "$HOME/Library/Caches/pip" \
    "${PYENV_ROOT:-}" \
    "${APPIMAGHE_CACHE:-}"
do
	[ "$d" -a -e "$d" ] && set -- "$@" "$d"
done

set -x
ls -Alh "$BUILD_PATH"
ls -Alh "$DIST_PATH"
[ "$1" ] && du -sch "$@"
