#!/bin/sh

version=$(grep version setup.py|cut -d"'" -f 2)
if [ "x${version#*-}" = "x$version" ]; then
    git tag -a v$version -m "Release $version"
else
    git tag -a v$version -m "Pre-release $version"
fi
echo "Remember to push tags: git push --tags"
