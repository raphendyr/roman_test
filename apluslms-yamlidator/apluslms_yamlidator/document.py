import logging
from abc import ABCMeta
from copy import deepcopy
from hashlib import sha1
from operator import attrgetter
from os import makedirs
from os.path import dirname, exists

from .utils.collections import Changes, MutableMapping, Sequence
from .utils.version import parse_version
from .utils.yaml import Dict, rt_dump_all as dump_all, rt_load_all as load_all


logger = logging.getLogger(__name__)


def hash(data):
    if isinstance(data, str):
        data = data.encode('utf-8')
    return sha1(data).digest()


def find_ml(current, keys):
    if isinstance(keys, str):
        keys = keys.split('.')
    elif not isinstance(keys, list):
        keys = list(keys)
    for key in keys[:-1]:
        if isinstance(current, Sequence):
            try:
                key = int(key)
            except ValueError:
                pass
        try:
            current = current[key]
        except KeyError:
            current = current.setdefault(key, {})
    return current, keys[-1]


class Versioned:
    _version_key = 'version'

    def __init__(self, path, version_key=None, allow_missing=False):
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
            yield self._document_class(self, index, data, version)

    def _getitem(self, index):
        if index < 0:
            raise IndexError('negative indexes are not accepted')
        version, data = self._documents[index]
        document = self._document_class(self, index, data, version)
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

    def get_latest(self, max_version=None):
        if self._version_key:
            if max_version is not None:
                max_version = parse_version(max_version)
                versions = [v for v in self._versions if v <= max_version]
            else:
                versions = self._versions.keys()
            version = max(versions, default=None)
            if not version:
                raise KeyError(max_version)
            return self._getitem(self._versions[version])
        return self._getitem(len(self._documents) - 1)

    def save(self):
        documents = [data for version, data in self._documents]
        try:
            content = dump_all(documents)
        except Exception:
            logger.error("YAML dump_all failed for %s", documents)
            raise
        hash_ = hash(content)
        if hash_ != self._hash:
            if self._dir and not exists(self._dir):
                logger.debug("Creating path: %s", self_dir)
                makedirs(self._dir)
            with open(self.path, 'w') as f:
                f.write(content)
            self._hash = hash_
            logger.debug("Wrote %d documents to %s", len(self._documents), self.path)


    def __repr__(self):
        return "<%s('%s')>" % (
            self.__class__.__name__,
            self.path,
        )


class DocumentMeta(ABCMeta):
    def __new__(metacls, name, bases, namespace, **kwargs):
        container = namespace.pop('Container', None)
        container_args = ('version_key')
        extras = {k: namespace.pop(k) for k in container_args if k in namespace}

        for arg in container_args:
            namespace[arg] = property(attrgetter('_'+arg))

        cls = super().__new__(metacls, name, bases, namespace, **kwargs)

        if container or extras:
            if not container:
                container = cls.Container
            container_namespace = {'_'+k: (extras.get(k) or getattr(container, '_'+k)) for k in container_args}
            container_namespace['_document_class'] = cls
            cls.Container = type(
                '%s-%s' % (name, container.__name__),
                (container,),
                container_namespace,
            )

        return cls


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
        if version is not None and document.version < version:
            document = document.upgrade(version)
        return document

    def __init__(self, container, index, data, version):
        self._container = container
        self._index = index
        self._data = Changes.wrap(data, parent=self)
        self._dirty = False
        self.version = version

    def data_updated(self, key, data):
        self._dirty = True

    @property
    def index(self):
        return self._index

    @property
    def path(self):
        return self._container.path

    def upgrade(self, version):
        version = parse_version(version)
        data = deepcopy(self._data.get_data())
        new = self.__class__(self._container, None, data, version)
        return new

    def save(self):
        if not self._dirty:
            return False

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
        self._container.save()
        self._dirty = False
        return True

    def __repr__(self):
        return "<%s%r(version=%s, data=%r)>" % (
            self.__class__.__name__,
            self._container,
            self.version,
            self._data,
        )

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

    def mlget(self, keys, default=None):
        container, key = find_ml(self._data, keys)
        return container.get(key, default)

    def mlset(self, keys, value):
        container, key = find_ml(self._data, keys)
        container[key] = value

    def mlsetwork(self, keys, value):
        container, key = find_ml(self._data, keys)
        return container.setwork(key, value)

    def mlsetdefault(self, keys, value):
        container, key = find_ml(self._data, keys)
        return container.setdefault(key, value)
