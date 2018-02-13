from os import getuid, getegid
from os.path import isdir, join

from .backends import BuildTask, BuildStep, Environment
from .helpers import import_string, cached_property
from .observer import StreamObserver


def clean_image_name(image):
    if ':' not in image:
        image += ':latest'
    return image


class Builder:
    def __init__(self, engine, config, observer=None):
        assert isdir(config.__path__), "Course configuration path doesn't exists"
        self.config = config
        self.path = config.__path__
        self._engine = engine
        self._observer = observer or StreamObserver()

    def build(self):
        backend = self._engine.backend
        observer = self._observer
        steps = [BuildStep.from_config(step) for step in self.config.steps]
        task = BuildTask(self.path, steps)

        observer.enter_prepare()
        backend.prepare(task, observer)
        observer.enter_build()
        result = backend.build(task, observer)
        observer.done(data=result)
        return result


class Engine:
    def __init__(self, backend_class=None):
        if not backend_class:
            from .backends.docker import DockerBackend as backend_class
        if isinstance(backend_class, str):
            backend_class = import_string(backend_class)
        environment = Environment(getuid(), getegid())
        self.backend = backend_class(environment)

    def verify(self):
        return self.backend.verify()

    def version_info(self):
        return self.backend.version_info()

    def create_builder(self, *args, **kwargs):
        return Builder(self, *args, **kwargs)
