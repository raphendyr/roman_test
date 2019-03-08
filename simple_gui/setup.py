#!/usr/bin/env python3
import importlib.util
from os import path
from setuptools import setup, find_packages

def _import(name, *parts):
    spec = importlib.util.spec_from_file_location(name, path.join(*parts))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

here = path.abspath(path.dirname(__file__))
core = _import('setup', path.dirname(here), 'setup.py')

info = core.INFO.copy()
info.update(dict(
    name=core.NAME + '-tki',
    version=core.get_version(here, 'roman_tki.py')[0],
    description=info['description']+', tkinter gui',
    long_description=core.read(here, 'README.rst'),

    zip_safe=False,
    #packages=find_packages(exclude=['contrib', 'docs', 'tests']),
    py_modules=['roman_tki'],
    install_requires=[
        core.core_requirement(core.NAME),
    ],
    entry_points={
        'console_scripts': [
            'roman-tki = roman_tki:main',
        ],
    },
))
setup(**info)
