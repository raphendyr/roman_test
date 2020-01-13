from abc import abstractmethod
from os import remove
from os.path import join

from apluslms_yamlidator.document import Document
from apluslms_yamlidator.validator import ValidationError

from . import CACHE_DIR

class CacheFile(Document):

    @property
    @abstractmethod
    def name(self):
        raise NotImplementedError

    @property
    @abstractmethod
    def schema(self):
        raise NotImplementedError

    @property
    @abstractmethod
    def version(self):
        raise NotImplementedError

    @classmethod
    def load(cls, **kwargs):
        path = join(CACHE_DIR, '%s.yml' % (cls.name,))
        if 'allow_missing' not in kwargs:
            kwargs['allow_missing'] = True
        try:
            return super().load(path, **kwargs)
        except ValidationError:
            remove(path)
            return super().load(path, **kwargs)

    def validate(self, quiet=True):
        super().validate(quiet)
