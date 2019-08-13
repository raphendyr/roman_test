import logging
from abc import ABCMeta
from copy import deepcopy
from enum import Enum
from hashlib import sha1
from itertools import chain, zip_longest
from os import makedirs
from os.path import dirname, exists

from .utils import convert_to_boolean as to_bool
from .utils.collections import Changes, MutableMapping, Sequence, recursive_update
from .utils.functional import attrproxy
from .utils.version import parse_version
from .utils.yaml import Dict, rt_dump as dump, rt_dump_all as dump_all, rt_load_all as load_all
from .utils.translation import _
from .validator import ValidationError, Validator


logger = logging.getLogger(__name__)

_NoDefault = object()


def hash(data):
    if isinstance(data, str):
        data = data.encode('utf-8')
    return sha1(data).digest()


def find_ml(current, keys, *, create_dicts=False):
    if isinstance(keys, str):
        keys = keys.split('.')
    elif not isinstance(keys, (tuple, list)):
        keys = tuple(keys)
    for i, key in enumerate(keys[:-1]):
        if isinstance(current, Sequence):
            try:
                key = int(key)
            except ValueError:
                pass
        try:
            current = current[key]
        except KeyError as err:
            if not create_dicts:
                raise KeyError('.'.join(keys[:i+1])) from err
            current = current.setdefault(key, {})
    key = keys[-1]
    if isinstance(current, (Sequence)) and not isinstance(current, str):
        key = int(key)
    return current, key


class Versioned:
    _schema = None
    _validator_manager = None
    _version_key = 'version'

    @classmethod
    def get_validator(cls, version):
        if cls._schema:
            validator = cls._validator_manager or Validator.get_default()
            return validator.get_validator(cls._schema, *version)
        elif cls._validator_manager:
            raise TypeError("{}._validator_manager is set, but ._schema is missing".format(cls.__name__))
        return None

    def __init__(self, path, *, version_key=None, allow_missing=False):
        self.path = path
        self._dir = dirname(path)
        if version_key is not None:
            self._version_key = version_key

        try:
            with open(path, 'r') as f:
                content = f.read()
        except FileNotFoundError:
            if not allow_missing:
                raise
            self._hash = b''
            self._documents = []
            self._versions = {}
        else:
            self._hash = hash(content)
            pv = self._parse_version
            self._documents = [(pv(data), data)
                               for data in load_all(content)]
            self._versions = {ver: idx
                              for idx, (ver, data) in enumerate(self._documents)}
            logger.debug("Read %d documents from %s", len(self._documents), path)

    def exists(self):
        return bool(self._documents)

    def _parse_version(self, data):
        if self._version_key:
            return parse_version(data.get(self._version_key, '1'))
        return None

    def __len__(self):
        return len(self._documents)

    def __iter__(self):
        documents = [(version, idx, data) for idx, (version, data) in enumerate(self._documents)]
        documents.sort()
        for version, index, data in documents:
            # NOTE: validation is skipped when iterating
            yield self._document_class(self, index, data, version)

    def _getitem(self, index, validate=True):
        if index < 0:
            raise IndexError('negative indexes are not accepted')
        version, data = self._documents[index]
        document = self._document_class(self, index, data, version)
        if version is not None and validate:
            document.validate()
        return document

    def _setitem(self, index, data):
        if index < 0:
            raise IndexError('negative indexes are not accepted')
        version, _ = self._documents[index]
        self._documents[index] = (version, data)

    def _additem(self, data, version):
        index = len(self._documents)
        self._documents.append((version, data))
        self._versions[version] = index
        return index

    def get_latest(self, max_version=None, validate=True):
        if self._version_key:
            if max_version is not None:
                max_version = parse_version(max_version)
                versions = [v for v in self._versions if v <= max_version]
            else:
                versions = self._versions.keys()
            version = max(versions, default=None)
            if not version:
                raise KeyError(max_version)
            return self._getitem(self._versions[version], validate=validate)
        return self._getitem(len(self._documents) - 1, validate=validate)

    def save(self, overwrite=True):
        documents = [data for version, data in self._documents]
        try:
            content = dump_all(documents)
        except Exception:
            logger.error("YAML dump_all failed for %s", documents)
            raise
        hash_ = hash(content)
        if hash_ != self._hash:
            if self._dir and not exists(self._dir):
                logger.debug("Creating path: %s", self._dir)
                makedirs(self._dir)
            with open(self.path, 'w' if overwrite else 'x') as f:
                f.write(content)
            self._hash = hash_
            logger.debug("Wrote %d documents to %s", len(self._documents), self.path)


    def __repr__(self):
        return "<%s['%s']('%s')>" % (
            self.__class__.__name__,
            self._schema,
            self.path,
        )

class DocumentMeta(ABCMeta):
    CONTAINER_ATTRS = ('schema', 'validator_manager', 'version_key')

    def __new__(metacls, name, bases, namespace, **kwargs):
        container = namespace.pop('Container', None)
        extras = {k: namespace.pop(k) for k in metacls.CONTAINER_ATTRS if k in namespace}

        for arg in metacls.CONTAINER_ATTRS:
            namespace[arg] = attrproxy('__class__', arg)

        version = namespace.get('version')
        if version is not None and not isinstance(version, property):
            namespace['version'] = parse_version(version)

        cls = super().__new__(metacls, name, bases, namespace, **kwargs)

        if not container:
            container = cls.Container
        container_namespace = {'_'+k: (extras.get(k) or getattr(container, '_'+k)) for k in metacls.CONTAINER_ATTRS}
        container_namespace['_document_class'] = cls
        cls.Container = type(
            '%s-%s' % (name, container.__name__),
            (container,),
            container_namespace,
        )

        return cls

for arg in DocumentMeta.CONTAINER_ATTRS:
    setattr(DocumentMeta, arg, attrproxy('Container', '_'+arg))


class Document(MutableMapping, metaclass=DocumentMeta):
    Container = Versioned
    version = None

    @classmethod
    def bind(cls, **kwargs):
        return type('Bound'+cls.__name__, (cls,), kwargs)

    @classmethod
    def load(cls, path, version=None, **kwargs):
        container = cls.Container(path, **kwargs)
        if version is None and getattr(cls, 'version', None) is not None:
            version = cls.version
        try:
            document = container.get_latest(max_version=version)
        except KeyError:
            document = cls(container, None, Dict(), version)
            document.initialize_data()
            document.validate()
        if version is not None and document.version < version:
            document = document.upgrade(version)
        return document

    @classmethod
    def create(cls, filename):
        document = cls.load(filename, allow_missing=True)
        document.save(overwrite=False)
        return document

    def initialize_data(self):
        vkey = self.version_key
        if vkey:
            self[vkey] = str(self.version)

    def __init__(self, container, index, data, version):
        self._container = container
        self._index = index
        self._data = Changes.wrap(data, parent=self)
        self._dirty = False
        self.version = version

    def data_updated(self, key, data):
        self._dirty = True

    @property
    def container(self):
        return self._container

    @property
    def index(self):
        return self._index

    @property
    def dir(self):
        return self._container._dir

    @property
    def path(self):
        return self._container.path

    @property
    def validator(self):
        if self.version is None:
            raise ValueError("Unable to a create validate for a document without version info")
        return self.Container.get_validator(self.version)

    @property
    def validator_id(self):
        validator = self.validator
        return validator.ID_OF(validator.schema)

    def validate(self, quiet=False):
        validator = self.validator
        if validator:
            try:
                validator.validate(self._data)
            except ValidationError as err:
                err.schema_id = id_ = validator.ID_OF(validator.schema)
                if not quiet:
                    logger.error(
                        _("A document '%s' does not validate against schema %s"),
                        self._container.path, id_
                    )
                parent = err.parent.instance if err.parent is not None else self._data
                path = err.path
                msg = err.message
                if "Additional properties are not allowed" in msg:
                    msg = msg.split("'")
                    path.append(msg[1])
                if err.path:
                    data, key = find_ml(parent, err.path)
                    if hasattr(data, '_data'):
                        data = data.get_data()
                    try:
                        if isinstance(data, (list, Sequence)):
                            line, column = data.lc.item(int(key))
                        elif (isinstance(data[key], (list, Sequence))
                                and not isinstance(data, str)):
                            line, column = data.lc.key(key)
                        else:
                            line, column = data.lc.value(key)
                        err.source = (self._container.path, line, column)
                    # if the document wasn't read from a file, it won't have lc
                    except Exception:
                        err.source = '.'.join(str(part) for part in err.path)

                raise err

    def upgrade(self, version):
        version = parse_version(version)
        data = deepcopy(self._data.get_data())
        new = self.__class__(self._container, None, data, version)
        return new

    class SaveOutput(Enum):
        NO_SAVE = 0
        SAVED_CHANGES = 1
        CREATED_FILE = 2

    def save(self, overwrite=True):
        if not self._dirty and exists(self.path):
            return self.SaveOutput.NO_SAVE
        file_exists = self.container.exists()

        data = self._data.get_data()
        vkey = self.version_key
        if vkey:
            missing = vkey not in data
            data[vkey] = str(self.version)
            if missing and hasattr(data, 'move_to_end'):
                data.move_to_end(vkey, last=False)
        if self._index is not None:
            self._container._setitem(self._index, data)
        else:
            self._index = self._container._additem(data, self.version)
        self._container.save(overwrite)
        self._dirty = False
        return self.SaveOutput.SAVED_CHANGES if file_exists else self.SaveOutput.CREATED_FILE

    def __repr__(self):
        return "<%s%r(version=%s, data=%r)>" % (
            self.__class__.__name__,
            self._container,
            self.version,
            self._data,
        )

    def find_type(self, keys):
        if isinstance(keys, str):
            key_list = keys.split(".")
        elif not isinstance(keys, list):
            key_list = list(keys)

        schema_keys = list(chain.from_iterable(zip_longest((), key_list, fillvalue='properties')))

        try:
            container, key = find_ml(self.validator.schema, schema_keys)
        except KeyError:
            return None

        if key in container:
            container = container[key]
            if "type" in container:
                return container["type"]
        return None

    # MutableMapping

    def setdefault(self, key, value):
        return self._data.setdefault(key, value)

    def __getitem__(self, key):
        return self._data[key]

    def __setitem__(self, key, value):
        self._data[key] = value

    def __delitem__(self, key):
        del self._data[key]

    def __iter__(self):
        yield from self._data

    def __len__(self):
        return len(self._data)

    def __contains__(self, key):
        return key in self._data

    def items(self):
        return self._data.items()

    def keys(self):
        return self._data.keys()

    def values(self):
        return self._data.values()

    # Multi-level interface

    def mlget(self, keys, default=_NoDefault):
        try:
            container, key = find_ml(self._data, keys)
            return container[key]
        except KeyError as err:
            if default is _NoDefault:
                raise KeyError(keys) from err
            return default

    def mlset(self, keys, value):
        container, key = find_ml(self._data, keys, create_dicts=True)
        try:
            container[key] = value
        except IndexError as err:
            err.index = key
            raise err

    def mlset_cast(self, keys, value):
        val_type = self.find_type(keys)

        if val_type:
            if val_type == "boolean":
                try:
                    value = to_bool(value)
                except ValueError as err:
                    err.value_type = val_type
                    raise err
            elif val_type == "integer":
                try:
                    value = int(value)
                except ValueError as err:
                    err.value_type = val_type
                    raise err
            elif val_type == "string" and not isinstance(value, str):
                err = ValueError()
                err.value_type = val_type
                raise err

        self.mlset(keys, value)

    def mlsetwork(self, keys, value):
        container, key = find_ml(self._data, keys, create_dicts=True)
        return container.setwork(key, value)

    def mlsetdefault(self, keys, value):
        container, key = find_ml(self._data, keys, create_dicts=True)
        return container.setdefault(key, value)

    def mldel(self, keys):
        container, key = find_ml(self._data, keys)
        del container[key]

    def recursive_update(self, new_data):
        recursive_update(self, new_data)
