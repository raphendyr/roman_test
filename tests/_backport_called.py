import sys
from unittest.mock import NonCallableMock


if sys.version_info < (3, 6):
    print("!! Backported Mock.assert_called() and Mock.assert_called_once()", file=sys.stderr)

    # backported from cPython 3.7
    if not hasattr(NonCallableMock, 'assert_called'):
        def assert_called(self):
            """assert that the mock was called at least once
            """
            if self.call_count == 0:
                msg = ("Expected '%s' to have been called." %
                       self._mock_name or 'mock')
                raise AssertionError(msg)
        NonCallableMock.assert_called = assert_called

    # backported from cPython 3.7
    if not hasattr(NonCallableMock, 'assert_called_once'):
        def assert_called_once(self):
            """assert that the mock was called only once.
            """
            if not self.call_count == 1:
                msg = ("Expected '%s' to have been called once. Called %s times.%s"
                       % (self._mock_name or 'mock',
                          self.call_count,
                          self._calls_repr()))
                raise AssertionError(msg)
        NonCallableMock.assert_called_once = assert_called_once
