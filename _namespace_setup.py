#!/usr/bin/env python3
# This file should be linked from a namespaced package
import importlib.util
from os import path

def _import(name, *parts):
    spec = importlib.util.spec_from_file_location(name, path.join(*parts))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

here = path.abspath(path.dirname(__file__))
root = path.dirname(path.dirname(here))
core = _import('setup', root, 'setup.py')

if __name__ == '__main__':
    core.setup_namespace(here)
