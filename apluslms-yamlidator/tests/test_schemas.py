import unittest
from unittest.mock import mock_open, patch

from apluslms_yamlidator import schemas


class TestGetText(unittest.TestCase):

    def test_get_text_returns_string(self):
        test_str = "a test string"
        test_raw = test_str.encode('utf-8')
        test_fn = "test/path"
        with patch('builtins.open', mock_open(read_data=test_raw)) as mock_fh:
            self.assertEqual(schemas.get_text(test_fn), test_str)
            mock_fh.assert_called_once()


class TestCheckExt(unittest.TestCase):

    def test_one_extension_matches(self):
        self.assertTrue(schemas.check_ext('test.py', ('.txt', '.py', '.js')))

    def test_no_matching_extension(self):
        self.assertFalse(schemas.check_ext('test.py', ('.txt', '.pyc', '.js')))


# FIXME: logging should be captured better. check nose.Logcapture
@patch(schemas.__name__+'.logger')
class TestWriteSchema(unittest.TestCase):

    def test_when_directory_does_not_exists_it_is_created(self, logger):
        n = schemas.__name__
        with patch(n+'.exists', return_value=False) as mock_exists, \
             patch(n+'.makedirs', side_effect=IOError()) as mock_makedirs, \
             patch('builtins.open', mock_open()) as mock_fn:

            schemas.write_schema('dir', 'name', True)
            mock_exists.asset_called_once_with('dir')
            mock_makedirs.assert_called_once_with('dir')
            mock_fn.assert_not_called()

    def test_schema_is_written_to_correct_file(self, logger):
        n = schemas.__name__
        with patch(n+'.exists', return_value=True), \
             patch(n+'.makedirs', side_effect=IOError()), \
             patch('builtins.open', mock_open()) as mock_fh:

            schemas.write_schema('dir', 'name', True)
            args, _kwargs = mock_fh.call_args
            self.assertEqual(args[0], 'dir/name.json')

    def test_correct_schema_data_is_written(self, logger):
        n = schemas.__name__
        with patch(n+'.exists', return_value=True), \
             patch(n+'.makedirs', side_effect=IOError()), \
             patch('builtins.open', mock_open()) as mock_fh:

            schemas.write_schema('dir', 'name', [1, 2, 3])
            val = ''.join(a[0] for a, kw in mock_fh().write.call_args_list)
            self.assertEqual(val, '[1, 2, 3]')
