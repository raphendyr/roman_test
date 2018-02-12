from os import getuid, getegid
from os.path import isdir, join

from .backends import BuildStep, Environment
from .logging import SimpleOutput
from .helpers import import_string, cached_property


def clean_image_name(image):
    if ':' not in image:
        image += ':latest'
    return image


class Builder:
    def __init__(self, config, backend=None, output=None):
        assert isdir(config.__path__), "Course configuration path doesn't exists"
        self.config = config
        self.path = config.__path__
        self.output = output or SimpleOutput()

        if not backend:
            from .backends.docker import DockerBackend
            backend = DockerBackend
        if isinstance(backend, str):
            backend = import_string(backend)
        self._backend_class = backend

    @cached_property
    def _backend(self):
        environment = Environment(self.path, getuid(), getegid())
        return self._backend_class(environment)

    @cached_property
    def _steps(self):
        steps = self.config.steps
        build_steps = []
        for step in steps:
            if isinstance(step, dict):
                if 'img' not in step:
                    raise RuntimeError("Missing image name (img) in step configuration: {}".format(step))
                bstep = BuildStep(
                    clean_image_name(step['img']),
                    step.get('cmd'),
                    step.get('mnt'),
                    step.get('env'),
                )
            else:
                bstep = BuildStep(clean_image_name(step), None, None, None)
            build_steps.append(bstep)

        return build_steps

    def build(self):
        steps = self._steps
        output = self.output
        backend = self._backend

        backend.prepare(self._steps, output)
        backend.build(self._steps, output)
