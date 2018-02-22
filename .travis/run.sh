#!/bin/sh -e
set -x

if [ "$TRAVIS_OS_NAME" = 'osx' ]; then
	#pyenv
	PYENV_VERSION=${PYENV_VERSION:-$TRAVIS_PYTHON_VERSION}
	[ "$PYENV_VERSION" ] || { echo "Missing env PYENV_VERSION"; exit 1; }
	PYENV_ROOT="$HOME/.pyenv-roman"
	PATH="$PYENV_ROOT/bin:$PATH"
	hash -r
	eval "$(pyenv init -)"
	hash -r
	PYENV_VERSION=$(pyenv install --list|tr -d '[ \t]'|grep "^$PYENV_VERSION"|tail -n1)
fi

python -m compileall -f .
python setup.py test
