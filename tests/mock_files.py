from unittest.mock import mock_open, patch, MagicMock

from apluslms_yamlidator.utils.yaml import load as yaml_loads


def _mock_open(*args, **kwargs):
    mock = mock_open(*args, **kwargs)
    def get_written_content():
        mock.return_value.write.assert_called()
        return ''.join(a[0] for a, kw in mock.return_value.write.call_args_list)
    mock.get_written_content = get_written_content
    mock.get_written_yaml = lambda: yaml_loads(get_written_content())
    return mock


class VFS(dict):
    """
    mock_files creates a dictionary containing all open files in it's
    context. The dictionary works as a virtual filesystem (VFS) without
    any paths, thus all base filenames needs to be unique. The VFS is
    returned by the context manager.

    Contents returned via open call can be passed in `files` dictionary.

        with mock_files() as vfs:
            # To check if file was written to:
            vfs['filename'].return_value.write.called
            # To check contents:
            vfs['filename.txt'].get_written_content() == "hello!"
            # To load yaml data:
            vfs['filename.yml'].get_written_yaml() == {'hello': 'world'}

            # VFS also contains mocks for listdir and isfile
            vfs.mock_isfile.assert_called()
            vfs.mock_listdir.assert_called()
    """
    def __init__(self, files):
        super().__init__(
            (fn.rsplit('/', 1)[-1], _mock_open(read_data=data))
            for fn, data in files.items()
        )
        self.mock_listdir = MagicMock(side_effect=lambda x: list(self))
        self.mock_isfile = MagicMock(side_effect=self.__contains__)
        self.mock_exists = MagicMock(side_effect=self.__contains__)

    def __contains__(self, fn):
        fn = fn.rsplit('/', 1)[-1]
        return super().__contains__(fn)

    def mock_open(self, fn, mode='r', *args, **kwargs):
        basename = fn.rsplit('/', 1)[-1]
        try:
            return self[basename](fn, mode, *args, **kwargs)
        except KeyError:
            if 'r' in mode:
                raise FileNotFoundError(fn)
            self[basename] = m = _mock_open()
            return m(fn, mode, *args, **kwargs)
