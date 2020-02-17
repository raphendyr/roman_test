#!/bin/sh -eu
cd "$(dirname "$0")"
cd ..

. ./scripts/_include.sh

export BUILD_CLI=true
export BUILD_GUI=true
export BUILD_SDIST=true
export BUILD_WHEEL=true
export TRAVIS_OS_NAME="$OS_NAME"
export TRAVIS_PYTHON_VERSION='3.7'
export TRAVIS_TAG=$(git describe)
export USE_VIRTUALENV=true

if [ "$OS_NAME" = 'osx' ]; then
	if ! [ "$(which brew)" ]; then
		export PYENV_ROOT="$HOME/.pyenv-roman"
	fi
	export PYENV_VERSION=$TRAVIS_PYTHON_VERSION
fi

.travis/install.sh && \
.travis/build_and_test.sh && \
.travis/build_releases.sh && \
:
ret=$?

remove_setup_cfgs $PACKAGES simple_gui

exit $ret
