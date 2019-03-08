. scripts/_include.sh

if [ "${INSTALL_SCRIPT:-}" != 'true' ]; then
	activate_python
fi

print_header() {
	echo "############################################################"
	echo "### $@"
	echo "############################################################"
}

print_step() {
	echo " ## $@ ##"
}
