# OS

if [ "${TRAVIS_OS_NAME:-}" ]; then
	OS_NAME=$TRAVIS_OS_NAME
else
	case "$(uname -s)" in
		Linux*)  OS_NAME=linux;;
		Darwin*) OS_NAME=osx;;
		CYGWIN*) OS_NAME=cygwin;;
		MINGW*)  OS_NAME=mingw;;
		*) echo "Unknown OS: $(uname -s)"; exit 1;;
	esac
fi


# Project PATHs

find_root() {
	(
		while [ "$PWD" != '/' ]; do
			if [ -e 'packages.txt' ]; then
				echo "$PWD"
				break
			fi
		done
	)
}

ROOT_PATH=$(find_root)
if [ -z "$ROOT_PATH" ]; then
	echo "Failed to find root path, including 'packages.txt'. You called the script from $PWD"
	exit 2
fi

BUILD_PATH=$ROOT_PATH/build
DIST_PATH=$ROOT_PATH/dist
EGG_INFO_PATH=$BUILD_PATH
EGG_PATH=$BUILD_PATH/eggs


# Python

PYTHON_VERSION_=${PYTHON_VERSION:-${PYENV_VERSION:-${TRAVIS_PYTHON_VERSION:-3}}}
PYTHON_VERSION=$(echo "$PYTHON_VERSION_"|cut -d. -f1-2)
PYTHON="python$PYTHON_VERSION"
if [ -z "$(which $PYTHON)" ] || ! $PYTHON --version >/dev/null 2>&1; then
	PYTHON_VERSION=$(echo "$PYTHON_VERSION"|cut -d. -f1)
	PYTHON="python$PYTHON_VERSION"
	if [ -z "$(which $PYTHON)" ] || ! $PYTHON --version >/dev/null 2>&1; then
		echo "Failed to find Python executable for $PYTHON_VERSION_" >&2
		exit 1
	fi
fi

PYTHONPATH="$ROOT_PATH/packaging/lib:$EGG_PATH"
export PYTHONPATH

python_module_exists() {
	$PYTHON -c "import sys, pkgutil; sys.exit(not pkgutil.find_loader('${1}'))"
}

python_remove_caches() {
	[ -e "$1" ] || return 0
	find "$1" -type f -name '*.py[co]' -exec rm -f -- '{}' +
	find "$1" -type d -name '__pycache__' -exec rmdir -- '{}' +
}

if [ "$OS_NAME" = 'osx' -a "${PYENV_VERSION:-}" ]; then
	. "$ROOT_PATH/scripts/_pyenv_osx.sh"
else
	. "$ROOT_PATH/scripts/_virtualenv.sh"
fi


# Utilities to work with multiple packages

PACKAGES=$(grep -vE '^\s*#' "$ROOT_PATH/packages.txt")

run_for() {
	package_path=$1; shift
	(
		cd "$package_path"
		"$@"
	)
}

run_for_all() {
	for package in $PACKAGES; do
		run_for "$package" "$@"
	done
}

write_setup_cfg() {
	cat > setup.cfg <<EOF
[easy_install]
install-dir = $EGG_PATH
exclude-scripts = 1

[build]
build-base = $BUILD_PATH/$(setup_py --name)
EOF
}

remove_setup_cfg() {
	[ -e setup.cfg ] && rm setup.cfg
}

remove_build_pycaches() {
	python_remove_caches "$BUILD_PATH/$(setup_py --name)/lib"
}

create_build_paths() {
	mkdir -p "$BUILD_PATH" "$EGG_INFO_PATH" "$DIST_PATH"
}

create_setup_cfgs() {
	for package in ${*:-$PACKAGES}; do
		run_for "$package" write_setup_cfg
	done
}

remove_setup_cfgs() {
	for package in ${*:-$PACKAGES}; do
		run_for "$package" remove_setup_cfg
	done
}

setup_py() {
	$PYTHON setup.py "$@"
}

setup_build() {
	setup_py build "$@"
}

setup_dist() {
	dist_command=$1; shift
	setup_py "$dist_command" --dist-dir "$DIST_PATH" "$@"
}

pyinst() {
	# Optimization needs to be set for Python interpreter (not pyinstaller).
	# Using -m PyInstaller would add CWD to sys.path, which would ignore
	# installed packages. As a workaround, we use pyinstaller script, which will
	# tell Python to add it's basedir to sys.path (e.g. venv/bin/). Result is
	# identical to calling pyinstaller directly.
	$PYTHON -OO $(which pyinstaller) --noconfirm --noconsole --workpath "$BUILD_PATH" --distpath "$DIST_PATH" "$@"
}
