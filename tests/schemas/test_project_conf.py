from ..test_cli import CliTestCase

class TestBackendValidation(CliTestCase):

    def test_basicBackend_shouldValidate(self):
        r = self.command_test('config -g', settings={
            'version': '1.0',
            'backends': {
                'docker1': {'type': 'docker', 'timeout': 50},
                'docker2': {'type': 'docker', 'timeout': 100}
            }
        })

    def test_dockerBackendWithNoType_shouldValidate(self):
        r = self.command_test('config -g', settings={
            'version': '1.0',
            'backends': {
                'docker': {'timeout': 50}
            }
        })

    def test_backendWithUnfamiliarType_shouldValidate(self):
        r = self.command_test('config -g', settings={
            'version': '1.0',
            'backends': {
                'backend1': {'type': 'unkown', 'asdf': True}
            }
        })

    def test_backendWithNoType_shouldFail(self):
        r = self.command_test('config -g', settings={
            'version': '1.0',
            'backends': {
                'backend1': {'test': True}
            }
        }, exit_code=1)
