import sys


class SimpleOutput:
    def __init__(self, manager_fmt=None, container_fmt=None, stream=None):
        self.mng_fmt = '{step:2d} : {msg}' if manager_fmt is None else manager_fmt
        self.cnt_fmt = '{step:2d} >> {msg}' if container_fmt is None else container_fmt
        self.stream = stream or sys.stdout

    def manager(self, step, msg):
        out = self.mng_fmt.format(step=step, msg=msg.rstrip())
        self.stream.write(out + '\n')

    def container(self, step, msg):
        out = self.cnt_fmt.format(step=step, msg=msg.rstrip())
        self.stream.write(out + '\n')
