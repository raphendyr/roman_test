#!/bin/sh -eu
cd "$(dirname "$0")"
cd ..

. scripts/_include.sh

create_setup_cfgs
run_for_all remove_build_pycaches
run_for_all setup_dist bdist_wheel
remove_setup_cfgs
