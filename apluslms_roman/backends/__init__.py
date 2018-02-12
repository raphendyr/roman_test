from collections import namedtuple


BuildStep = namedtuple('BuildStep', [
    'img', # docker image
    'cmd', # If not None, docker command
    'mnt', # If not None, course data is mounted to this path in RW mode
    'env', # If not None, dict that is given as environment for the image
])


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

    def prepare(self, steps, out):
        raise NotImplementedError

    def build(self, steps, out):
        raise NotImplementedError
