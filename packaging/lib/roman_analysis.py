import platform
from collections import namedtuple
from glob import glob
from os.path import dirname, join
from sys import version_info

from PyInstaller.utils.hooks import collect_data_files
from pkg_resources import parse_version
from setuptools import find_namespace_packages

Version = namedtuple('Version', ('lib', 'gui', 'full'))
Meta = namedtuple('Meta', ('exes', 'hiddens', 'datas', 'arch', 'version'))

def get_lib_meta(workpath):
    import apluslms_roman

    buildpath = dirname(workpath)
    exes = [join(dirname(apluslms_roman.__file__), '__main__.py')] # NOTE: __main__ uses absolute paths
    packages = []
    datas = []

    # include python packages from all build projects
    for lib in glob(join(buildpath, '*', 'lib')):
        packages.extend(find_namespace_packages(where=lib))

    # include package data files
    for package in packages:
        if '.' not in package:
            datas.extend(collect_data_files(package))

    # importlib_resources fix
    if version_info < (3, 7):
        import importlib_resources
        path = dirname(importlib_resources.__file__)
        datas.append((join(path, 'version.txt'), 'importlib_resources'))

    # find the version
    version = str(parse_version(apluslms_roman.__version__))
    arch = "%s-%s" % (platform.system(), platform.machine())
    return Meta(exes, packages, datas, arch, version)


def get_gui_meta(workpath):
    import roman_tki

    lib_meta = get_lib_meta(workpath)
    exes = [roman_tki.__file__]
    packages = list(lib_meta.packages)
    datas = list(lib_meta.datas)

    # find versions
    lib_version = lib_meta.version
    gui_version = str(parse_version(roman_tki.__version__))
    full_version = '%s-%s' % (gui_version, lib_version)
    version = Version(lib_version, gui_version, full_version)

    return Meta(exes, packages, datas, lib_meta.arch, version)
