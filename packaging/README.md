Packaging
=========

Currently, Travis CI is used to build release files to Github and PyPI.
We build source tarballs, wheels and executable GUI application.
Scripts for different parts are in [/scripts/](../scripts) and [/.travis/](../.travis).
Support files for executable bundles are here.


Known issues in packaging
-------------------------

* Source tarballs for sub projects do not contain valid setup.py
* We currently install wheels to ensure that valid version of a required sub package is installed, but we also add lib folders from build to the `PYTHONPATH`. Later one requires that we cleanup `__pycache__`s before building wheels, but first is overly complex.
