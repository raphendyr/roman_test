#!/bin/sh -eu
cd "$(dirname "$0")"
cd ..

. scripts/_include.sh

if [ -z "${VIRTUAL_ENV:-}" ]; then
    USE_VIRTUALENV=true
    install_python
    activate_python
    ./scripts/install_for_development.sh
fi

pip install -r requirements_test.txt

echo "Running all tests with $($PYTHON --version)"
#echo "----------------------------------------------------------------------"
run_tests() {
    echo
    title=$(setup_py --fullname)
    printf "%*s\n" $(((${#title}+70)/2)) "$title"
    echo "----------------------------------------------------------------------"
    $PYTHON -m unittest discover -b -t . -s tests
    echo
}
run_for_all run_tests
