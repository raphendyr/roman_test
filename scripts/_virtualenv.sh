VIRTUALENV_PATH="$BUILD_PATH/.venv"

install_python() {
	if [ "${USE_VIRTUALENV:-}" = 'true' -a ! -e "$VIRTUALENV_PATH/bin/activate" ]; then
		mkdir -p "$VIRTUALENV_PATH"
		if python_module_exists venv && python_module_exists ensurepip; then
			$PYTHON -m venv "$VIRTUALENV_PATH"
		elif python_module_exists virtualenv; then
			$PYTHON -m virtualenv -p $PYTHON "$VIRTUALENV_PATH"
		else
			echo "Option USE_VIRTUALENV=true requires venv or virtualenv module to be available for $PYTHON" >&2
			exit 1
		fi
	fi
}

activate_python() {
	if [ "${USE_VIRTUALENV:-}" = 'true' ]; then
		. "$VIRTUALENV_PATH/bin/activate"
		PYTHON='python3'
	fi
}
