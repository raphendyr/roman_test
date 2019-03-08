from collections import OrderedDict
from os import listdir
from os.path import basename, dirname, isfile, isdir, join

from apluslms_yamlidator.utils.yaml import dump as dump_yaml, load as load_yaml


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


class CourseConfig:
    @classmethod
    def find_from(cls, path, name=None, prefixes=None):
        if not name:
            name = DEFAULT_NAME
        if not prefixes:
            prefixes = DEFAULT_PREFIXES

        files = ['%s.%s' % (name, prefix) for prefix in prefixes]
        files_s = frozenset(files)

        if not isdir(path):
            raise CourseConfigError("Path {} doesn't exists or is not a directory".format(path))

        for filename in listdir(path):
            if filename in files_s:
                config = join(path, filename)
                if isfile(config):
                    break
        else:
            if is_legacy_configuration(path):
                return cls(LEGACY_CONFIG,
                           path=path,
                           source=LEGACY_SOURCE)
            raise CourseConfigError("Couldn't find course configuration from {}. Expected to find one of these: {}".format(path, ', '.join(files)))

        return cls.load_from(config)

    @classmethod
    def load_from(cls, filepath):
        if not isfile(filepath):
            raise CourseConfigError("Configuration file {} is not a file".format(filepath))

        with open(filepath) as f:
            config = load_yaml(f)

        return cls(config, path=dirname(filepath), source=filepath)

    # defaults:
    steps = ()

    def __init__(self, config, path, source=None, name=None):
        self.__path__ = path
        self.__source__ = source
        self.__config__ = config
        self.name = name or basename(path)


        if not isinstance(config, dict):
            raise CourseConfigError("Configuration from {} is invalid".format(source or '-'))

        for key, value in config.items():
            if key[0] == '_':
                raise CourseConfigError('Invalid option {} in configuration from {}'.format(key, source or '-'))
            setattr(self, key, value)


    def __str__(self):
        return "---\n" + dump_yaml(self.__config__)
