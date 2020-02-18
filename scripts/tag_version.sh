#!/bin/sh
cd "$(dirname "$0")"
cd ..

version=$(grep -E '^__version__\s*=' apluslms_roman/__init__.py|cut -d"'" -f 2)
if [ "x${version#*-}" = "x$version" ]; then
	git tag -a v$version -m "Release $version"
else
	git tag -a v$version -m "Pre-release $version"
fi
git tag -n1 v$version
echo "Remember to push the tag: git push origin v$version"
