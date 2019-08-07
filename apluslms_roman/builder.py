from os import environ, getuid, getegid, mkdir
from os.path import isdir
from shutil import rmtree

from apluslms_yamlidator.utils.decorator import cached_property
from apluslms_yamlidator.utils.collections import OrderedDict

from .backends import (
    BACKENDS,
    BackendContext,
    BuildResult,
    BuildStep,
    BuildTask,
)
from .observer import StreamObserver
from .utils.importing import import_string
from .utils.translation import _

class Builder:
    def __init__(self, engine, config, observer=None, environment=None):
        if not isdir(config.dir):
            raise ValueError(_("config.dir isn't a directory."))
        self.config = config
        self.path = config.dir
        self._engine = engine
        self._observer = observer or StreamObserver()
        self._environment = environment or []


    def get_steps(self, refs: list = None):
        steps = [BuildStep.from_config(i, step, self._environment)
            for i, step in enumerate(self.config.steps)]
        if refs:
            name_dict = {step.name: step for step in steps}
            refs = [int(ref) if ref.isdigit() else ref.lower() for ref in refs]
            # NOTE: May raise KeyError or IndexError
            steps = [steps[ref] if isinstance(ref, int) else name_dict[ref] for ref in refs]
            steps = list(OrderedDict.fromkeys(steps))
        return steps

    def build(self, step_refs: list = None, clean_build=False):
        backend = self._engine.backend
        observer = self._observer
        steps = self.get_steps(step_refs) # NOTE: may raise KeyError or IndexError
        try:
            task = BuildTask(self.path, steps)
            observer.enter_prepare()
            result = backend.prepare(task, observer)
            observer.result_msg(result)
            if result.ok:
                observer.enter_build()
                # FIXME: add support for other build paths
                if clean_build:
                    if isdir('_build'):
                        rmtree('_build')
                if clean_build or not isdir('_build'):
                    mkdir('_build')
                result = backend.build(task, observer)
                observer.result_msg(result)
            observer.done(result)
        except KeyboardInterrupt:
            return BuildResult(False)
        return result


class BackendError(Exception):

    def __init__(self, backend):
        super().__init__()
        self.backend = backend


class Engine:
    def __init__(self, backend_class=None, settings=None):
        backend_name = None
        if backend_class is None:
            if settings and 'backend' in settings:
                backend_class = settings['backend']
                if 'backends' in settings and backend_class in settings['backends']:
                    backend_name = backend_class
                    if 'type' in settings['backends'][backend_name]:
                        backend_class = settings['backends'][backend_name]['type']
            else:
                from .backends.docker import DockerBackend as backend_class
        if isinstance(backend_class, str):
            if '.' not in backend_class:
                backend_class = BACKENDS.get(backend_class, backend_class)
            try:
                backend_class = import_string(backend_class)
            except ImportError:
                raise BackendError(backend_class)
        self._backend_class = backend_class

        name = getattr(backend_class, 'name', None) or backend_class.__name__.lower()
        prefix = name.upper() + '_'
        options = {}
        # config
        if backend_name is not None:
            options.update({prefix + k.replace('-', '_').upper(): v
                for k, v in settings['backends'][backend_name].items()
                if k != 'type'})
        # environment
        options.update({k: v for k, v in environ.items() if k.startswith(prefix)})
        # command line
        if settings:
            options.update({prefix + k.replace('-', '_').upper(): v
                for k, v in settings.get(name, {}).items()})

        self._backend_context = BackendContext(getuid(), getegid(), options)

    @cached_property
    def backend(self):
        return self._backend_class(self._backend_context)

    def verify(self):
        return self.backend.verify()

    def version_info(self):
        return self.backend.version_info()

    def create_builder(self, *args, **kwargs):
        return Builder(self, *args, **kwargs)
