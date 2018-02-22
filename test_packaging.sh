#!/bin/sh -e

case "$(uname -s)" in
	Linux*)   machine=linux;;
	Darwin*)  machine=osx;;
	CYGWIN*)  machine=cygwin;;
	MINGW*)   machine=mingw;;
	*) echo "Unknown machine: $(uname -s)"; exit 1;;
esac

export TRAVIS_TAG=$(git describe)
export TRAVIS_PYTHON_VERSION=$(python3 --version|cut -d' ' -f2|cut -d. -f1-2)
export BUILD_DIST=true
export TRAVIS_OS_NAME=$machine

rm -rf test_env dist
python3 -m virtualenv -p python3 test_env
. ./test_env/bin/activate

.travis/install.sh
.travis/pre_deploy.sh
ret=$?

rm -rf test_env

exit $?
