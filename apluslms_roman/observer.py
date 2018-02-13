import sys
from enum import Enum


class Phase(Enum):
    NONE = 0
    PREPARE = 1
    BUILD = 2
    DONE = 10


class Message(Enum):
    ENTER = 0
    START_STEP = 1
    END_STEP = 2
    MANAGER_MSG = 11
    CONTAINER_MSG = 12


class BuildObserver:
    _state = Phase.NONE

    def _message(self, phase, type_, step=None, data=None):
        raise NotImplementedError

    def enter_prepare(self):
        self._state = Phase.PREPARE
        self._message(self._state, Message.ENTER)
    def enter_build(self):
        self._state = Phase.BUILD
        self._message(self._state, Message.ENTER)
    def done(self, data=None):
        self._state = Phase.DONE
        self._message(self._state, Message.ENTER, data=data)

    def start_step(self, step):
        self._message(self._state, Message.START_STEP, step)

    def end_step(self, step):
        self._message(self._state, Message.END_STEP, step)

    def manager_msg(self, step, msg):
        self._message(self._state, Message.MANAGER_MSG, step, msg)

    def container_msg(self, step, msg):
        self._message(self._state, Message.CONTAINER_MSG, step, msg)


class StreamObserver(BuildObserver):
    def __init__(self, stream=None):
        self.stream = stream or sys.stdout

    def _message(self, phase, type_, step=None, data=None):
        if type_ == Message.ENTER: return
        phase_s = '{} {:d}'.format(phase.name, step) if step is not None else phase.name
        if type_ == Message.CONTAINER_MSG:
            fmt = '{} >> {}'
        elif type_ == Message.MANAGER_MSG:
            fmt = '{} : {}'
        else:
            fmt = '{} {}'
        if not data: data = type_.name.lower()
        self.stream.write(fmt.format(phase_s, str(data).rstrip()) + '\n')
