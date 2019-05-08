from itertools import chain
from os import listdir
from os.path import join, isdir, isfile

from apluslms_yamlidator.document import Document
from apluslms_yamlidator.utils.collections import OrderedDict
from apluslms_yamlidator.utils.version import Version

from .utils.translation import _

DEFAULT_NAMES = ('roman', 'course')
DEFAULT_PREFIXES = ('yml', 'yaml', 'json')
DEFAULT_NAME = '%s.%s' % (DEFAULT_NAMES[0], DEFAULT_PREFIXES[0])

LEGACY_SOURCE = '<legacy a-plus-rst-tools support>'
LEGACY_CONFIG = OrderedDict((
    ('version', 2),
    ('theme', 'aplus'),
    ('steps', (OrderedDict((
        ('img', 'apluslms/compile-rst'),
        ('cmd', ('make', 'touchrst', 'html')),
        ('mnt', '/compile'),
        ('env', {'STATIC_CONTENT_HOST': "http://localhost:8080/static/default"}),
    ),),)),
))

class ProjectConfigError(Exception):
    pass

def is_legacy_configuration(path):
    """Checks if path is legacy a-plus-rst-tools course"""
    return isfile(join(path, 'conf.py')) and isfile(join(path, 'Makefile'))

class ProjectConfig(Document):
    name = 'roman_project'
    schema = name
    version = Version(2, 0)
    _version_key = "version"

    @classmethod
    def find_from(cls, path):

        files = [
            ['%s.%s' % (name, prefix) for prefix in DEFAULT_PREFIXES]
            for name in DEFAULT_NAMES
        ]
        files = list(chain.from_iterable(files))
        files_s = frozenset(files)

        if not isdir(path):
            raise ProjectConfigError(
                "Path {} doesn't exists or is not a directory".format(path)
            )

        for filename in listdir(path):
            if filename in files_s:
                config = join(path, filename)
                if isfile(config):
                    break
        else:
            if is_legacy_configuration(path):
                container = cls.Container(join(path, DEFAULT_NAME), allow_missing=True)
                return cls(container, None, LEGACY_CONFIG, cls.version)
            raise ProjectConfigError("Couldn't find project configuration from {}. Expected to find one of these: {}".format(path, ', '.join(files)))

        return cls.load(config)

    @property
    def steps(self):
        return self.setdefault('steps', [])

    @property
    def steps_by_name(self):
        return {s['name'].lower(): s for s in self.steps if 'name' in s}
