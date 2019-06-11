import unittest

from apluslms_roman.utils.importing import import_string


TEST_DATA = "foobar"


class TestImportString(unittest.TestCase):

    def test_invalid_import_string_raises_exception(self):
        with self.assertRaises(ImportError):
            import_string('tests.utils.test_importing.INVALID')

    def test_valid_import_string_returns_same_object(self):
        val = import_string('tests.utils.test_importing.TEST_DATA')
        self.assertIs(val, TEST_DATA)
