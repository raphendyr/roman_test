import logging
import re
from collections import OrderedDict
from collections.abc import Mapping, Sequence
from functools import lru_cache
from urllib.parse import quote_plus as quote, unquote_plus as unquote, urlsplit

from jsonschema import (
    RefResolver,
    ValidationError,
    validators,
)
from requests import get as requests_get

from .schemas import schema_registry
from .utils.error_render import render_lc
from .utils.translation import _
from .utils.version import Version


logger = logging.getLogger(__name__)

SCHEMA_FILENAME_RE = re.compile("^(.*)[_-]v?(\d+)[_.](\d+)$")


def get_remote_schema(uri):
    url = urlsplit(uri)
    if url.scheme not in ('http', 'https'):
        raise ValueError("Invalid schema protocol '{}': {}".format(url.scheme, uri))
    basename = quote(url.geturl())
    loader = schema_registry.find_file(basename)
    if loader is not None:
        return loader
    logger.debug("Requesting a schema from a url %s", uri)
    data = requests_get(uri).json()
    schema_registry.save_schema(basename, data)
    return data


def ref_wrap(loader, ref):
    def get():
        data = loader()
        schema = data.get('$schema', '')
        id_ = 'id' if '/draft-03/' in schema or '/draft-04/' in schema else '$id'
        data.setdefault(id_, ref)
        return data
    return get


class Validator:
    @classmethod
    def get_default(cls):
        if not hasattr(cls, '_default_instance') or not isinstance(cls._default_instance, cls):
            cls._default_instance = cls()
        return cls._default_instance

    def __init__(self, dirs=None):
        self._dirs = dirs
        self._ref_index = None
        self._local_index = None

    @property
    def _index(self):
        if self._local_index is None:
            self.update_indexes()
        return self._local_index

    @property
    def _schemas(self):
        if self._ref_index is None:
            self.update_indexes()
        return self._ref_index

    def update_indexes(self):
        # ref format = {ref_name: (loader, parser)}
        ref_index = {}
        # local format = {name: {(major, minor): ref}}
        local_index = {}

        schemas = schema_registry.schemas_with_dirs(self._dirs)
        for ref, loader in schemas.items():
            if ref.startswith('http%3A') or ref.startswith('https%3A'):
                ref_index.setdefault(unquote(ref), loader)
                continue
            match = SCHEMA_FILENAME_RE.match(ref)
            if match:
                name, major, minor = match.groups()
                major, minor = int(major), int(minor)
                ref1 = "{}-v{}.{}".format(name, major, minor)
                ref2 = "{}".format(ref)
                if ref1 not in ref_index:
                    ref_index[ref1] = ref_wrap(loader, ref1)
                    if ref1 != ref2:
                        ref_index[ref2] = ref_wrap(loader, ref2)
                    local_index.setdefault(name, {}).setdefault(Version(major, minor), ref1)
                continue

        self._ref_index = ref_index
        self._local_index = local_index
        self.get_schema.cache_clear()
        self.get_validator.cache_clear()

    def get_version(self, name, major, minor=None):
        """
        Find a schema with given 'major' and 'minor'.
        If minor is not defined, newest is selected.
        Returns the version and reference to the document.
        """
        schema_index = self._index.get(name)
        if schema_index is None:
            raise ValueError("No schemas found by name {!r}, search dirs: {}".format(name, self._dirs))

        if minor is not None and (major, minor) in schema_index:
            ver = (major, minor)
        else:
            versions = {v for v in schema_index if v.major == major}
            if minor is not None:
                versions = {v for v in versions if v.minor >= minor}
            if not versions:
                raise ValueError(_("A version {}.{} does not exist for schema {!r}, known versions: {}").format(
                    major,
                    "%d+" % minor if minor is not None else '*',
                    name,
                    ", ".join(str(v) for v in sorted(schema_index)),
                ))
            ver = max(versions)
        # version, schema reference
        return ver, schema_index[ver]

    @lru_cache(128)
    def get_schema(self, ref):
        try:
            return self._schemas[ref]()
        except KeyError:
            if urlsplit(ref).scheme in ('', 'file'):
                raise
        return get_remote_schema(ref)

    @lru_cache(32)
    def get_validator(self, schema_name, major, minor=None):
        _v, ref = self.get_version(schema_name, major, minor)
        schema = self.get_schema(ref)
        logger.debug("Creating validator for %s", ref)
        handlers = {scheme: self.get_schema for scheme in ('', 'file', 'http', 'https')}
        resolver = RefResolver.from_schema(schema, cache_remote=False, handlers=handlers)
        validator = _validator_for(schema)
        validator.check_schema(schema)
        return validator(schema, resolver=resolver)

    def validate(self, data, schema_name, major, minor=None):
        validator = self.get_validator(schema_name, major, minor)
        try:
            validator.validate(data)
        except ValidationError as e:
            logger.warning("Validation error: %s", e)
            return False
        else:
            logger.info("Validation ok: %s", schema_name)
            return True

    def __del__(self):
        for key in ['get_schema', 'get_validator']:
            f = getattr(self, key)
            logger.debug("%s: %s", key, f.cache_info())


def format_path(path):
    if not path:
        return ""
    if not isinstance(path, list):
        path = list(path)
    return path[0] + "".join([".%s" % p if isinstance(p, str) else "[%d]" % p for p in path[1:]])


def render_error(error, num_lines=5):
    out = []
    if hasattr(error, 'source'):
        if isinstance(error.source, str):
            out.append("\nError was caused by '{}'.".format(error.source))
        else:
            source, line, col = error.source
            out.extend(render_lc(source, line, col, num_lines))

    context = error.context
    if context:
        out.append("There were several errors:")
        for e in context:
            out.append("\nError at %s:" % format_path(error.path + e.path))
            out.append("  %s: %s" % (type(e).__name__, e.message))
    else:
        out.append("\n%20s: %s" % ("validator", error.validator))
        for k, v in error.schema.items():
            if k[0] == '$':
                continue
            if isinstance(v, list):
                v = [x for x in v if not isinstance(x, (dict, list))]
                if not v:
                    continue
            elif isinstance(v, dict):
                v = list(v.keys())
            out.append("%20s: %s" % (k, v))
    out.append("\n%s: %s" % (type(error).__name__, error.message))
    return out


## Meta schema updates

def _validator_with_default_feature(validator_class):
    validate_properties = validator_class.VALIDATORS["properties"]

    def set_defaults(validator, properties, instance, schema):
        for property, subschema in properties.items():
            if "default" in subschema:
                instance.setdefault(property, subschema["default"])
        yield from validate_properties(validator, properties, instance, schema)

    def python_type(validator, types, instance, schema):
        if not isinstance(types, list):
            types = [types]

        if not any(instance.__class__.__name__ == type_ for type_ in types):
            types = ["'%s'" % type_ for type_ in types]
            yield ValidationError("{} is not an instance of Python class {}"
                .format(instance, ', '.join(types)))

    new = validators.extend(validator_class,
        # redefine 'properties' validator
        validators={
            "properties" : set_defaults,
            "pythonType": python_type},
        # use collections.abc classes for array and object so Changes containers work too
        type_checker=validator_class.TYPE_CHECKER.redefine_many({
            'array': (lambda checker, instance:
                isinstance(instance, Sequence) and not isinstance(instance, str)),
            'object': (lambda checker, instance: isinstance(instance, Mapping)),
        }),
    )
    # set_defaults doesn't work when validating schemas themselfs
    new.check_schema = validator_class.check_schema
    return new


_meta_schemas = OrderedDict(
    (id_, _validator_with_default_feature(validator_class))
    for id_, validator_class in validators.meta_schemas.items()
)


def _validator_for(schema):
    if '$schema' not in schema:
        return next(reversed(_meta_schemas))
    return _meta_schemas[schema['$schema']]
