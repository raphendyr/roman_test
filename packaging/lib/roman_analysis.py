from collections import namedtuple
from glob import glob
from os.path import dirname, join
from sys import version_info

from pkg_resources import parse_version
from setuptools import find_namespace_packages

import apluslms_roman
import roman_tki


Version = namedtuple('Version', ('lib', 'gui', 'full'))
Meta = namedtuple('Meta', ('exes', 'hiddens', 'datas', 'version'))

def get_meta(workpath):
    buildpath = dirname(workpath)
    exes = [roman_tki.__file__]
    packages = []
    datas = []

    # include python packages from all build projects
    for lib in glob(join(buildpath, '*', 'lib')):
        packages.extend(find_namespace_packages(where=lib))

    # importlib_resources fix
    if version_info < (3, 7):
        import importlib_resources
        path = dirname(importlib_resources.__file__)
        datas.append((join(path, 'version.txt'), 'importlib_resources'))

    # find versions
    lib_version = str(parse_version(apluslms_roman.__version__))
    gui_version = str(parse_version(roman_tki.__version__))
    full_version = '%s-%s' % (gui_version, lib_version)
    version = Version(lib_version, gui_version, full_version)

    return Meta(exes, packages, datas, version)
