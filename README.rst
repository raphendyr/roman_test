Roman
=====

|build status| |download release|

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
Alternatively, you can install cli version via pip :code:`pip install apluslms-roman` (will add :code:`roman` command).

.. _releases page: https://github.com/apluslms/roman/releases


List of graphical user inteface binaries
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

* :code:`*-linux.AppImage` is an AppImage_ package of Roman.
  Download, mark file executable and run it.
  Requires FUSE_ (installed on typical linux desktop).
* :code:`*-linux.zip` contains a single-file executable.
  Download, extract, run :code:`roman`.
  Requires that files in :code:`/tmp/` can be executed.
* :code:`*-mac.dmg` contains *Roman.app* in a disk image.
  Download, open, drag *Roman.app* to e.g. *Applications*, run.
  **Note**: On the first time you need to right or control-click the app, select *open* in the menu and finally *open* in the dialog.
* :code:`*-mac.zip` contains *Roman.app* in a zip.
  Same prosess as with above version.

If you are not sure what file to use, then use the first one for your operating system.

.. _AppImage: https://appimage.org/
.. _FUSE: https://en.wikipedia.org/wiki/Filesystem_in_Userspace


.. badges: http://shields.io/

.. |build status| image:: https://img.shields.io/travis/apluslms/roman.svg
   :target: https://travis-ci.org/apluslms/roman

.. |download release| image:: https://img.shields.io/github/release/apluslms/roman.svg
   :target: https://github.com/apluslms/roman/releases
