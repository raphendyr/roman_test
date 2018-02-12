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

You can install roman via pip :code:`pip install git+https://github.com/apluslms/roman.git#egg=apluslms-roman`.
Alternatively you can download GUI binary from `releases page`_.

.. _releases page: https://github.com/apluslms/roman/releases


.. badges: http://shields.io/

.. |build status| image:: https://img.shields.io/travis/apluslms/roman.svg
   :target: https://travis-ci.org/apluslms/roman

.. |download release| image:: https://img.shields.io/github/release/apluslms/roman.svg
   :target: https://github.com/apluslms/roman/releases
