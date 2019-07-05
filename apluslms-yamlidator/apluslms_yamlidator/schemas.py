import logging
from codecs import open
from collections import OrderedDict
from importlib import import_module
from itertools import zip_longest
from json import dump as json_dumpf, loads as json_load
from os import (
    listdir,
    makedirs,
)
from os.path import (
    basename,
    dirname,
    exists,
    isdir,
    isfile,
    join,
    splitext,
)

from .utils.decorator import cached_property
from .utils.module_resources import get_module_resources, get_resource_text
from .utils.translation import _
from .utils.yaml import load as yaml_load


logger = logging.getLogger(__name__)


__all__ = (
    'schema_registry',
)


class SchemaError(Exception):
    pass


def get_text(path, **kwargs):
    if kwargs.get('encoding', None) is None:
        kwargs['encoding'] = 'utf-8'
    with open(path, **kwargs) as f:
        return f.read()


def check_ext(filename, extensions):
    return any(filename.endswith(e) for e in extensions)


def iter_paths(paths, extensions):
    for path, encoding in paths:
        if isfile(path):
            if check_ext(path, extensions):
                yield path, encoding
        elif isdir(path):
            for filename in sorted(listdir(path)):
                if check_ext(filename, extensions):
                    yield join(path, filename), encoding


def get_file_loader(path, encoding=None):
    name, ext = splitext(basename(path))
    parser = json_load if ext == 'json' else yaml_load
    def load():
        logger.debug("Reading a schema from '%s'", path)
        try:
            return parser(get_text(path, encoding=encoding))
        except Exception as error:
            logger.error(
                "Read operation for a schema from '%s' failed with %s: %s",
                path, error.__class__.__name__, error)
            raise SchemaError(path) from error
    return name, load


def get_resource_loader(module, filename):
    name, ext = splitext(filename)
    parser = json_load if ext == 'json' else yaml_load
    def load():
        logger.debug("Reading a schema from a package '%s:%s'", module, filename)
        try:
            return parser(get_resource_text(module, filename))
        except Exception as error:
            refname = "'%s:%s'" % (module, filename)
            try:
                # try to look up the file location
                path = join(dirname(import_module(module).__file__), filename)
            except Exception:
                pass
            else:
                refname += " (%s)" % (path,)
            logger.error(
                "Read operation for a schema from a package %s failed with %s: %s",
                refname, error.__class__.__name__, error)
            raise SchemaError(refname) from error
    return name, load


def write_schema(dir_, basename, data):
    if not exists(dir_):
        logger.debug("Creating the schema cache dir %s", dir_)
        try:
            makedirs(dir_)
        except IOError as e:
            logger.warning(_("Failed to create the schema cache dir %s: %s"), dir_, e)
            return
    path = join(dir_, basename) + '.json'
    logger.debug("Writing a schema to a cache file %s", path)
    try:
        with open(path, 'w') as f:
            json_dumpf(data, f)
    except IOError as e:
        logger.warning(_("Failed to safe the schema to a cache file %s: %s"), path, e)


class SchemaRegistry:
    extensions = ('json', 'yml', 'yaml')

    def __init__(self):
        self._modules = []
        self._paths = []
        self._cache = None

    def __iter__(self):
        yield from self.schemas

    def __len__(self):
        return len(self.schemas)

    def __contains__(self, name):
        return name in self.schemas

    def register_module(self, module):
        if module not in self._modules:
            self._modules.append(module)
        self.reload()

    def register_path(self, path, encoding=None):
        if path not in self._paths:
            self._paths.append((path, encoding))
        self.reload()

    def register_cache(self, path, encoding=None):
        self.register_path(path, encoding=encoding)
        self._cache = path

    def find_file(self, name):
        if name in self.schemas:
            return self.schemas[name]
        for dir_, encoding in self._paths:
            base = join(dir_, name)
            for ext in self.extensions:
                path = base + '.' + ext
                if isfile(path):
                    return self.get_file_loader(path, encoding)
        return None

    def get_file_loader(self, path, encofing=None):
        name, loader = get_file_loader(path, encoding)
        # NOTE: can set wrong path, if schemas is out of date
        self.schemas.setdefault(name, loader)
        return loader

    def get_resource_loader(self, module, filename):
        name, loader = get_resource_loader(module, filename)
        # NOTE: can set wrong path, if schemas is out of date
        self.schemas.setdefault(name, loader)
        return loader

    @cached_property
    def schemas(self):
        schemas = OrderedDict()
        # NOTE: paths are sorted, thus json > yaml > yml
        for path, encoding in iter_paths(self._paths, self.extensions):
            name, loader = get_file_loader(path, encoding)
            schemas.setdefault(name, loader)
        for module in self._modules:
            for filename in sorted(get_module_resources(module, self.extensions)):
                name, loader = get_resource_loader(module, filename)
                schemas.setdefault(name, loader)
        return schemas

    def schemas_with_dirs(self, dirs, encoding=None):
        if not dirs:
            return self.schemas
        schemas = OrderedDict(self.schemas)
        paths = zip_longest(dirs, (), fillvalue=encoding)
        for path, encoding in iter_paths(paths, self.extensions):
            name, loader = get_file_loader(path, encoding)
            schemas.setdefault(name, loader)
        return schemas

    def reload(self):
        self.__dict__.pop('schemas', None)

    def save_schema(self, basename, data):
        self.schemas.setdefault(basename, lambda: data)
        if self._cache:
            write_schema(self._cache, basename, data)

schema_registry = SchemaRegistry()
