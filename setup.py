#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
"""A setuptools based setup module.

See:
https://packaging.python.org/en/latest/distributing.html
https://github.com/pypa/sampleproject
"""

import os, re, sys
from codecs import open
from distutils.version import StrictVersion
from functools import lru_cache
from glob import glob
from os import path
from pkg_resources import parse_version
from setuptools import __version__ as setuptools_version, find_namespace_packages, find_packages, setup

if StrictVersion(setuptools_version) < StrictVersion('20.2'):
    print('Your setuptools version does not support PEP 508. Have you installed requirements_build.txt?', file=sys.stderr)
    sys.exit(1)


ROOT = path.abspath(path.dirname(__file__))


def read(*file):
    assert file, "Mising filename"
    try:
        with open(path.join(*file), encoding='utf-8') as f:
            return f.read()
    except IOError:
        return ''


def _coerce_requirements(args):
    if not args:
        args = (ROOT,)
    if not args[-1].endswith('.txt'):
        args = tuple(args) + ('requirements.txt',)
    return args


def read_requirements(*file):
    file = _coerce_requirements(file)
    reqs = (l.split('#', 1)[0].strip() for l in read(*file).splitlines())
    return [l for l in reqs if l]


def get_version(*file):
    match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]", read(*file), re.M)
    if match:
        version = parse_version(match.group(1))
        major, minor, *_ = version._version.release + (0,)
        return (str(version), major, minor)
    raise RuntimeError("Unable to find version string.")


@lru_cache(maxsize=512)
def is_core_package(name: str):
    if name == NAME:
        return True
    return path.exists(path.join(ROOT, name, 'setup.py'))


@lru_cache(maxsize=512)
def find_core_packages(name: str):
    if not is_core_package(name):
        raise ValueError("Can not find packges for {}, as it is not a core package".format(name))
    return find_packages(
        where=path.join(ROOT, name),
        exclude=('dist*', 'build*', 'tests*'),
    )


@lru_cache(maxsize=512)
def get_core_version(name: str):
    for module in find_core_packages(name):
        try:
            return get_version(ROOT, name, *module.split('.'), '__init__.py')
        except (IOError, RuntimeError):
            pass
    return VERSION


# this hack skips version requirement when called from pip3
if os.environ.get('_', '').endswith('pip3') and sys.argv == ['-c', 'egg_info']:
    def core_requirement(name: str):
        return name
else:
    def core_requirement(name: str):
        version, major, minor = get_core_version(name)
        fmt = "{0} >= {1}, <{2}" if major > 0 else "{0} == {1}"
        return fmt.format(name, version, major+1)


def get_requirements(*file):
    return [core_requirement(req) if ' ' not in req and is_core_package(req) else req
            for req in read_requirements(*file)]


def get_extra_requirements(*file, sep='-'):
    file = _coerce_requirements(file)
    *where, filename = file
    base, ext = path.splitext(filename)
    extras = {}
    for extras_file in glob(path.join(*where, base+sep+'*'+ext)):
        name = path.splitext(path.basename(extras_file))[0].split(sep, 1)[1]
        reqs = get_requirements(extras_file)
        if reqs:
            extras[name] = reqs
    return extras


def parse_rst_field(text: str, *fields):
    def find():
        it = iter(text.splitlines())
        for line in it:
            if line and line[0] == ':' and line.split(':', 2)[1].lower() in fields:
                yield line.split(':', 2)[2].strip()
                break
        for line in it:
            if not line or line[0] == ':':
                break
            yield line.strip()
    return ' '.join(find())


def basic_info(where):
    info = INFO.copy()
    info.pop('description', None)
    text = read(where, 'README.rst')
    if text:
        info['long_description'] = text
        for key, fields in INFO_FIELDS:
            value = parse_rst_field(text, *fields)
            if value:
                info[key] = value
    info['install_requires'] = get_requirements(where)
    return info


def setup_package(where, name=None, **kwargs):
    if not name:
        name = path.basename(where)

    info = basic_info(where)
    info.setdefault('description', "A support package for {}".format(NAME))
    info.setdefault('long_description', "This is a support package for {}".format(NAME))
    info['name'] = name
    info['version'] = get_core_version(name)[0]
    info['packages'] = find_core_packages(where)
    info.update(**kwargs)
    setup(**info)


def _find_namespace(where):
    dir_ = path.join(where, MODULE)
    files = [(fn, path.join(dir_, fn)) for fn in os.listdir(dir_)]
    dirs = [fn for fn, fp in files if path.isdir(fp)]
    if len(dirs) != 1:
        raise RuntimeError("Unable to autodetect the namespace as there are multiple dirs in {}".format(dir_))
    return dirs[0]


def setup_namespace(where, name=None, namespace=None, **kwargs):
    """A helper to create a simple namespaced setup file"""
    if not name:
        name = path.basename(where)
    if not namespace:
        namespace = _find_namespace(where)

    info = basic_info(where)
    info.setdefault('description', "{}, module .{}.{}".format(INFO['description'], namespace, name))
    info.setdefault('long_description', "This is a module to the namespace {}.{}".format(MODULE, namespace))
    info['name'] = '-'.join((NAME, namespace, name))
    info['packages'] = ['.'.join((MODULE, namespace, name))]
    info.update(kwargs)
    setup(**info)


NAME = 'apluslms-roman'
MODULE = 'apluslms_roman'
VERSION = get_version(ROOT, MODULE, '__init__.py')
README = read(ROOT, 'README.rst')
INFO_FIELDS = (
    ('description', ('abstract', 'description')),
    ('author', ('author',)),
)
INFO = dict(
    version=VERSION[0],
    keywords='apluslms material',
    url='https://github.com/apluslms/roman',
    author_email='apluslms@googlegroups.com',
    license='MIT',
    platforms=['any'],

    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 4 - Beta',
        'License :: OSI Approved :: MIT License',

        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Topic :: Software Development :: Build Tools',
        'Topic :: Software Development :: Libraries :: Python Modules',

        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3 :: Only',
    ],

    include_package_data = True,
    package_data={
        '': [
            '*.json',
            '*.yaml',
            '*.yml',
        ],
    },

    test_suite='tests',
)
INFO.update((key, parse_rst_field(README, *fields))  for key, fields in INFO_FIELDS)


if __name__ == '__main__':
    packages = find_packages(include=[MODULE, MODULE+'.*'])
    packages.extend(find_namespace_packages(include=[MODULE+'.s.*']))
    setup(
        name=NAME,
        long_description=README,
        install_requires=get_requirements(),
        extras_require=get_extra_requirements(),
        packages=packages,
        entry_points={
            'console_scripts': [
                'roman = apluslms_roman.cli:main',
            ],
        },
        zip_safe=False,
        **INFO,
    )
