import sys

from unittest.mock import NonCallableMock

if sys.version_info < (3, 6):
    print("Paching assert_called and assert_called_once to Mock")

    def assert_called(self):
        """assert that the mock was called at least once
        """
        if self.call_count == 0:
            msg = ("Expected '%s' to have been called." %
                   self._mock_name or 'mock')
            raise AssertionError(msg)
    NonCallableMock.assert_called = assert_called

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

