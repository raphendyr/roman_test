if [ "${OS_NAME:-}" != 'osx' ]; then
	echo "WARNING: You are running/sourcing _pyenv_osx.sh file, which is designed only for macOS installations, so you are probably making a mistake." >&2
fi

PYENV_VERSION=${PYENV_VERSION:-$TRAVIS_PYTHON_VERSION}
if [ -z "$PYENV_VERSION" ]; then
	echo "Missing env PYENV_VERSION" >&2
	exit 1
fi

brew_install_or_upgrade() {
	if ! brew list $1 >/dev/null 2>&1; then
		brew install $1
	elif [ "${INSTALL_SCRIPT:-}" = 'true' ] && brew outdated | grep $1 >/dev/null; then
		brew upgrade $1
	fi
}

git_clone_or_upgrade() {
	if [ ! -e "$1/.git" ]; then
		[ -e "$1" ] && rm -rf "$1"
		git clone "$2" "$1"
	elif [ "${INSTALL_SCRIPT:-}" = 'true' ]; then
		(
			cd "$1"
			git remote set-url origin "$2"
			git fetch origin
			git reset -q --hard origin/master
		)
	fi
}

PYENV_GIT_URL=${PYENV_GIT_URL:-https://github.com/pyenv/pyenv.git}

if [ -z "$(which pyenv)" -o "${INSTALL_SCRIPT:-}" = 'true' ]; then
	if [ -z "$(which brew)" -o "${PYENV_ROOT:-}" ]; then
		export PYENV_ROOT=${PYENV_ROOT:-$HOME/.pyenv}
		if [ "${PATH#*$PYENV_ROOT*}" = "$PATH" ]; then
			export PATH="$PYENV_ROOT/bin:$PATH"
		fi

		git_clone_or_upgrade "$PYENV_ROOT" "$PYENV_GIT_URL"
	else
		brew_install_or_upgrade pyenv
	fi
fi

hash -r
eval "$(pyenv init -)"
hash -r

PYENV_VERSION=$(pyenv install --list|tr -d '[ \t]'|grep "^$PYENV_VERSION"|tail -n1)
if [ -z "$PYENV_VERSION" ]; then
	pyenv install --list
	echo "No requested Python version available. List of supported versions is above"
	exit 1
fi

export PYENV_VERSION


PYENV_VIRTUALENV_NAME=$(echo "${PWD#/}" | tr '/' '_')

. "$ROOT_PATH/scripts/_virtualenv.sh"

eval "virtualenv_$(declare -f install_python)"

install_python() {
	PYTHON_CONFIGURE_OPTS="--enable-framework" pyenv install -s "$PYENV_VERSION"

	virtualenv_install_python
}
