#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
"""A setuptools based setup module.

See:
https://packaging.python.org/en/latest/distributing.html
https://github.com/pypa/sampleproject
"""

import re
from setuptools import setup, find_packages
# To use a consistent encoding
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

with open(path.join(here, 'requirements.txt'), encoding='utf-8') as f:
    requirements = f.read().splitlines()
    requirements = [l.split('#', 1)[0].strip() for l in requirements]
    requirements = [l for l in requirements if l]

def find_version(*file_paths):
    with open(path.join(here, *file_paths), 'r') as fp:
        match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]", fp.read(), re.M)
        if match:
            return match.group(1)
    raise RuntimeError("Unable to find version string.")

setup(
    name='apluslms-roman',
    version=find_version('apluslms_roman', '__init__.py'),
    description='Course material builder for online learning systems',
    long_description=long_description,
    keywords='apluslms material',
    url='https://github.com/apluslms/roman',
    author='Jaakko Kantojärvi',
    author_email='jaakko.kantojarvi@aalto.fi',
    license='MIT',

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
        'Programming Language :: Python :: 3 :: Only',
    ],

    zip_safe=True,
    packages=find_packages(exclude=['contrib', 'docs', 'tests']),
    include_package_data = True,
    package_data={
        '': ['*.json'],
    },

    install_requires=requirements,

    entry_points={
        'console_scripts': [
            'roman = apluslms_roman.cli:main',
        ],
    },
)
