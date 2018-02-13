from collections import namedtuple

from ..observer import BuildObserver


BuildTask = namedtuple('BuildTask', [
    'path',
    'steps',
])


def clean_image_name(image):
    if ':' not in image:
        image += ':latest'
    return image


class BuildStep:
    """
    img: docker image
    cmd: If not None, docker command
    mnt: If not None, course data is mounted to this path in RW mode
    env: If not None, dict that is given as environment for the image
    """
    __slots__ = ('img', 'cmd', 'mnt', 'env')

    @classmethod
    def from_config(cls, data):
        if isinstance(data, dict):
            if 'img' not in data:
                raise RuntimeError("Missing image name (img) in step configuration: {}".format(data))
            img = clean_image_name(data['img'])
            return cls(img, data.get('cmd'), data.get('mnt'), data.get('env'))
        else:
            return cls(clean_image_name(data), None, None, None)

    def __init__(self, img, cmd, mnt, env):
        self.img, self.cmd, self.mnt, self.env = img, cmd, mnt, env


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
    'uid',
    'gid',
])


class Backend:
    WORK_SIZE = '100M'
    WORK_PATH = '/work'

    def __init__(self, environment: Environment):
        self.environment = environment

    def prepare(self, task: BuildTask, observer: BuildObserver):
        raise NotImplementedError

    def build(self, task: BuildTask, observer: BuildObserver):
        """
            Returns BuildResult
        """
        raise NotImplementedError

    def verify(self):
        """Verify that connections to backend is working
        Returns:
          On success: None
          On failure: exception or error string
        """
        raise NotImplementedError

    def version_info(self):
        pass
