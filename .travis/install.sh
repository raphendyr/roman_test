#!/bin/sh -e
set -x

if [ "$TRAVIS_OS_NAME" = 'osx' ]; then
	# pyenv repo
	PYENV_ROOT=$HOME/.pyenv-roman
	if [ ! -e "$PYENV_ROOT/.git" ]; then
		[ -e "$PYENV_ROOT" ] && rm -rf "$PYENV_ROOT"
		git clone https://github.com/yyuu/pyenv.git "$PYENV_ROOT"
	else
	   (cd "$PYENV_ROOT"; git pull)
	fi

	# pyenv env
	PATH="$PYENV_ROOT/bin:$PATH"
	hash -r
	eval "$(pyenv init -)"
	hash -r

	# python version
	PYENV_VERSION=$(pyenv install --list|tr -d '[ \t]'|grep "^$PYENV_VERSION"|tail -n1)
	if [ -z "$PYENV_VERSION" ]; then pyenv install --list; exit 1; fi
	PYTHON_CONFIGURE_OPTS="--enable-framework" pyenv install -s $PYENV_VERSION


	pip install wheel
fi

pip install -r requirements.txt
pip install -r requirements_test.txt
