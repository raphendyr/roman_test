Roman
=====

|build status| |download release|

:Abstract: Course material builder for online learning systems
:Author: Jaakko Kantojärvi <jaakko.kantojarvi@aalto.fi>

Roman is course material builder for A+ and other learning management systems.
Roman uses docker_ to run different build steps.
Course building steps are configure in :code:`course.yml`, which is read by roman.

.. _docker: https://www.docker.com/

**Roman is in experimental development state**

Check out :code:`Ariel`.
It is an extension to sphinx build process that is used to build RST course material to HTML and YAML files.
It can simple be used by adding :code:`apluslms/ariel` to build steps.


Course configuration
--------------------

Roman reads configuration file :code:`course.yml`, :code:`course.yaml` or :code:`course.json` and then
runs course build steps defined in :code:`steps` list.
Steps can be strings describing docker image or objects containing at least :code:`img`.
Here is small example:

.. code-block:: yaml

  # course.yml
  ---
  version: 2
  theme: aplus

  steps:
    - hello-world
    - img: apluslms/compile-rst
      cmd: make touchrst html
      mnt: /compile
      env:
        STATIC_CONTENT_HOST: "http://localhost:8080/static/default"


Installation
------------

You can use prebuild binaries with graphical user inteface from `releases page`_.
Alternatively, you can install cli version via pip ``pip3 install --user apluslms-roman[docker]``, which will add ``$HOME/.local/bin/roman``.
Presuming you have that in your ``PATH``, then you can execute ``roman --help`` to get started.

.. _releases page: https://github.com/apluslms/roman/releases


List of graphical user inteface binaries
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

* ``*-linux.AppImage`` is an AppImage_ package of Roman.
  Download, mark file executable and run it.
  Requires FUSE_ (installed on typical linux desktop).
* ``*-linux.zip`` contains a single-file executable.
  Download, extract, run ``roman``.
  Requires that files in ``/tmp/`` can be executed.
* ``*-mac.dmg`` contains *Roman.app* in a disk image.
  Download, open, drag *Roman.app* to e.g. *Applications*, run.
  **Note**: On the first time you need to right or control-click the app, select *open* in the menu and finally *open* in the dialog.
* ``*-mac.zip`` contains *Roman.app* in a zip.
  Same prosess as with above version.

If you are not sure what file to use, then use the first one for your operating system.

*Documentation on how these files are build, can be found under ``packaging`` in the source repo.*

.. _AppImage: https://appimage.org/
.. _FUSE: https://en.wikipedia.org/wiki/Filesystem_in_Userspace


Developing
----------

This repository curently holds few different python packages, which makes things problematic.
There is set of scripts under ``./scripts/`` to make this ok.

For example, you can setup development environment for you:

.. code-block:: sh

    # install venv (you can skip this part)
    python3 -m venv venv
    # or
    python3 -m virtualenv -p python3 venv
    # activate
    . ./venv/bin/activate

    # install roman packages
    ./scripts/install_for_development.sh

To run tests:

.. code-block:: sh

    # run all tests in the repo
    #  creates virtual env, if none is active
    ./scripts/run_all_tests.sh

    # run all tests for a package
    python3 setup.py test
    python3 -m unittest discover -t . -s tests

    # run a single test file
    python3 -m unittest tests.test_cli

    # run a single test class
    python3 -m unittest tests.test_cli.TestGetConfig





.. badges: http://shields.io/

.. |build status| image:: https://travis-ci.com/apluslms/roman.svg?branch=master
   :target: https://travis-ci.com/apluslms/roman

.. |download release| image:: https://img.shields.io/github/release/apluslms/roman.svg
   :target: https://github.com/apluslms/roman/releases
