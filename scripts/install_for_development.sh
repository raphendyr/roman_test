#!/bin/sh -e
cd "$(dirname "$0")"
cd ..

set --
[ "$VIRTUAL_ENV" ] || set -- --user

pip3 install "$@" -r requirements_build.txt
pip3 install "$@" -r requirements-docker.txt

for p in $(grep -vE '^\s*#' packages.txt); do
	set -- "$@" -e "$p"
	[ -e "$p/setup.cfg" ] && rm "$p/setup.cfg"
done
pip3 install "$@"
