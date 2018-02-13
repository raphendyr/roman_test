from collections import namedtuple


BuildStep = namedtuple('BuildStep', [
    'img', # docker image
    'cmd', # If not None, docker command
    'mnt', # If not None, course data is mounted to this path in RW mode
    'env', # If not None, dict that is given as environment for the image
])


class BuildResult:
    __slots__ = ('code', 'error', 'step')

    def __init__(self, code=0, error=None, step=None):
        self.code = code
        self.error = error
        self.step = step
        assert self.ok or step is not None, "step is required for failed result"

    @property
    def ok(self):
        return self.code == 0 and self.error is None

    def __str__(self):
        if self.ok:
            return "Build ok"
        error = self.error or 'exit code {}'.format(self.code)
        return "Build failed on step {}: {}".format(self.step, error)


Environment = namedtuple('Environment', [
    'course_path',
    'uid',
    'gid',
])


class Backend:
    WORK_SIZE = '100M'
    WORK_PATH = '/work'

    def __init__(self, environment):
        self.environment = environment

    def prepare(self, steps, observer):
        raise NotImplementedError

    def build(self, steps, observer):
        """
            Returns BuildResult
        """
        raise NotImplementedError
