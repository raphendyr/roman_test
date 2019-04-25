from os import listdir
from os.path import join, isdir, isfile

from apluslms_yamlidator.document import Document
from apluslms_yamlidator.utils.collections import OrderedDict
from apluslms_yamlidator.utils.version import Version

from .utils.translation import _

DEFAULT_NAME = 'course'
DEFAULT_PREFIXES = ('yml', 'yaml', 'json')

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

class CourseConfigError(Exception):
    pass

def is_legacy_configuration(path):
    """Checks if path is legacy a-plus-rst-tools course"""
    return isfile(join(path, 'conf.py')) and isfile(join(path, 'Makefile'))

class CourseConfig(Document):
    name = 'course_config'
    schema = name
    version = Version(2, 0)

    @classmethod
    def find_from(cls, path, name=None, prefixes=None):
        if not name:
            name = DEFAULT_NAME
        if not prefixes:
            prefixes = DEFAULT_PREFIXES

        files = ['%s.%s' % (name, prefix) for prefix in prefixes]
        files_s = frozenset(files)

        if not isdir(path):
            raise CourseConfigError(
                "Path {} doesn't exists or is not a directory".format(path)
            )

        for filename in listdir(path):
            if filename in files_s:
                config = join(path, filename)
                if isfile(config):
                    break
        else:
            if is_legacy_configuration(path):
                container = cls.Container(config, allow_missing=True)
                return cls(container, None, LEGACY_CONFIG, cls.version)
            raise CourseConfigError("Couldn't find course configuration from {}. Expected to find one of these: {}".format(path, ', '.join(files)))

        return cls.load(config)

    @property
    def dir(self):
        return self._container._dir

    @property
    def steps(self):
        return self.get('steps') or []
