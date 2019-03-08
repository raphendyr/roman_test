#!/bin/sh -e

INSTALL_SCRIPT=true
. .travis/_include.sh

print_header "Install dependencies"

if [ "$OS_NAME" = 'linux' -a "$TRAVIS" = 'true' ]; then
    print_step "System packages"
    sudo apt-get -qqy install appstream || true
fi

print_step "Installing environment"
create_build_paths
install_python
activate_python
pip install --upgrade pip setuptools wheel

# setup.py and build requirements
print_step "Installing build dependencies"
pip install -r requirements_build.txt
[ -e "requirements_build_$TRAVIS_OS_NAME.txt" ] && pip install -r "requirements_build_$TRAVIS_OS_NAME.txt"

# test requirements
print_step "Installing test dependencies"
pip install -r requirements_test.txt

# generate setup.cfg files
print_step "Writing setup.cfg to all packages"
create_setup_cfgs $PACKAGES simple_gui
