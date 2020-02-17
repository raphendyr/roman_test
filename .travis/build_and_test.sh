#!/bin/sh -e

. .travis/_include.sh

print_header "Test and install packages"

build_and_test() {
	if [ -e "$1/requirements.txt" ]; then
		print_step "Installing requirements for $1"
		pip install -r "$1/requirements.txt"
	fi

	print_step "Building package $1"
	run_for "$1" setup_py build

	if [ -d "$1/tests" ]; then
		print_step "Running tests for $1"
		run_for "$1" setup_py test
	else
		print_step "No tests for $1"
	fi
}

install() {
	name=$(run_for "$1" setup_py --name)
	print_step "Building wheel $name from $1"
	python_remove_caches "$BUILD_PATH/$name/lib"
	run_for "$1" setup_dist bdist_wheel

	wname=$(echo "$name" | tr '-' '_')
	wversion=$(run_for "$1" setup_py --version)
	extras=$(cd "$1" && ls requirements-*.txt 2>/dev/null|sed -e 's/^requirements-//' -e 's/\.txt$//'|tr '\n' ','|sed 's/,$//')
	[ "$extras" ] && extras="[$extras]"
	print_step "Installing $wname-$wversion $extras"
	for wheel in "$DIST_PATH/$wname-$wversion"*; do
		pip install "$wheel$extras"
		[ "${BUILD_WHEEL:-}" = 'true' ] || rm "$wheel"
	done
}

for package in $PACKAGES; do
	build_and_test "$package"
	install "$package"
done

if [ "${BUILD_GUI:-}" = 'true' ]; then
	build_and_test "simple_gui"
	install "simple_gui"
fi
