import sys
from contextlib import contextmanager, ExitStack
from collections import namedtuple

from io import StringIO
from json import dumps as json_dumps
from os.path import abspath, dirname, join
from shlex import split as shlex_split
from traceback import format_exc
from unittest import TestCase
from unittest.mock import patch, MagicMock

from apluslms_roman import cli
from .mock_files import VFS


@contextmanager
def capture_output():
    new_out, new_err = StringIO(), StringIO()
    old_out = (sys.stdout, cli.stdout)
    old_err = (sys.stderr, cli.stderr)
    try:
        sys.stdout = cli.stdout = new_out
        sys.stderr = cli.stderr = new_err
        yield (sys.stdout), (sys.stderr)
    finally:
        sys.stdout, sys.stderr = old_out[0], old_err[0]
        cli.stdout, cli.stderr = old_out[1], old_err[1]

COURSE = join(dirname(__file__), 'mock_course')
# NOTE: some tests presume these to be defaults
SETTINGS_FN = 'roman_settings.yml'
CONFIG_FN = 'roman.yml'

HELLO_CONFIG = {
    'version': '2.0',
    'steps': [{
        'img': 'hello-world',
        'name': 'hello'
    }]
}


class CliTestCase(TestCase):
    CommandResult = namedtuple('CommandResult', ('out', 'err', 'files'))

    # the setUp and tearDown methods prevent ResourceWarnings from happening
    def setUp(self):
        self.patch_stack = ExitStack().__enter__()
        # disable Engine, so cli actions don't accidentally start one
        self.patch_stack.enter_context(patch('apluslms_roman.cli.Engine'))

    def tearDown(self):
        self.patch_stack.close()

    def command_test(self, *command, config=None, config_fn=None,
            settings=None, exit_code=0):
        files = {}
        args = []

        if config:
            if not isinstance(config, str):
                config = json_dumps(config)
            files[config_fn or CONFIG_FN] = config
        if config_fn:
            args.extend(('--file', config_fn))
        if settings:
            if not isinstance(settings, str):
                settings = json_dumps(settings)
            files[SETTINGS_FN] = settings
            args.extend(('--config', SETTINGS_FN))

        if len(command) == 1 and isinstance(command[0], str):
            command = shlex_split(command[0])
        args.extend(command)

        class CliExit(Exception):
            pass

        with ExitStack() as ctx:
            _e = ctx.enter_context
            _p = lambda *a, **kw: _e(patch(*a, **kw))
            # disable '_build' folder fix
            _p('apluslms_roman.builder.isdir', return_value=True)
            # mock cli exit, so SystemExit is not raised and we get return code directly
            exit_mock = _p('apluslms_roman.cli.exit', side_effect=CliExit)
            # mock files
            vfs = VFS(files)
            _p('builtins.open', vfs.mock_open)
            _p('apluslms_roman.configuration.listdir', vfs.mock_listdir)
            _p('apluslms_roman.configuration.isfile', vfs.mock_isfile)
            _p('apluslms_roman.configuration.isdir', return_value=True)
            _p('apluslms_yamlidator.document.exists', vfs.mock_exists)
            _p('apluslms_yamlidator.document.makedirs')
            # capture stdio
            out, err = ctx.enter_context(capture_output())

            try:
                # call main
                with self.assertRaises(CliExit, msg="cli.main() didn't call cli.exit()"):
                    cli.main(args=args)

                # check exit
                exit_mock.assert_called_once()
                exit_args = exit_mock.call_args[0]
                if exit_code is not None:
                    returned_code = exit_args and exit_args[0] or 0
                    self.assertEqual(returned_code, exit_code,
                        msg="cli.main exited with unexpect return code")

                # cli.exit writes message to stderr, but it was mocked..
                if len(exit_args) == 2:
                    print(exit_args[1], file=err)
                return self.CommandResult(out.getvalue(), err.getvalue(), vfs)
            except Exception as e:
                if exit_mock.called:
                    exit_args = exit_mock.call_args[0]
                    returned_code = exit_args and exit_args[0] or 0
                else:
                    returned_code = '?'
                raise AssertionError(
                    ("cli.main({!r}) -> {} raised an exception\n\n{}\n"
                    "Roman output:\n{}\n{}").format(
                        args,
                        returned_code,
                        format_exc(limit=-10),
                        out.getvalue().strip(),
                        err.getvalue().strip(),
                    ))



class TestGetConfig(CliTestCase):

    def test_get_config(self):
        config = {'version': '2',
            'steps': [{'img': 'hello-world'}]}
        r = self.command_test('config', config=config)
        self.assertIn("---\n# roman settings", r.out)
        self.assertIn("---\n# project config", r.out)
        self.assertEqual(r.err, "")

    def test_get_missing_config(self):
        r = self.command_test('config', config=None, exit_code=1)
        self.assertIn("Couldn't find project configuration from", r.err)
        self.assertIn("You can create a configuration file with", r.err)

    def test_get_invalid_config(self):
        invalid = "version: '2'\ninvalid: value\n"
        r = self.command_test('config', config=invalid, exit_code=1)
        self.assertIn("\nValidationError:", r.err)


@patch('apluslms_roman.cli.Engine', **{
    'return_value.verify.return_value': None,
    'return_value.create_builder.return_value.build.return_value': MagicMock(
        'apluslms_roman.backends.BuildResult', **{
            'ok': True, 'code': 0, 'error': None, 'step': None,
            '__str__.return_value': 'test build ok',
        },
    ),
})
class TestBuildAction(CliTestCase):

    def test_build(self, EngineMock):
        _ = self.command_test('build', config=HELLO_CONFIG)

        engine = EngineMock.return_value
        engine.create_builder.assert_called_once()
        builder_config = engine.create_builder.call_args[0][0]
        self.assertEqual(builder_config.steps[0]['img'], 'hello-world')

        builder = engine.create_builder.return_value
        builder.build.assert_called_once_with(None)

    def test_build_empty(self, EngineMock):
        r = self.command_test('build', config={'version': '2'}, exit_code=1)
        self.assertEqual(r.out.strip(), "Nothing to build.")

        engine = EngineMock.return_value
        engine.create_builder.assert_called_once()
        builder_config = engine.create_builder.call_args[0][0]
        self.assertEqual(len(builder_config.steps), 0)

        builder = engine.create_builder.return_value
        builder.build.assert_not_called()

    def test_build_with_steps(self, EngineMock):
        for step in ('hello', '0'):
            EngineMock.reset_mock()
            with self.subTest(step=step):
                self.command_test('build', '--steps', step, config=HELLO_CONFIG)

                engine = EngineMock.return_value
                builder = engine.create_builder.return_value
                builder.build.assert_called_once()
                self.assertListEqual(list(builder.build.call_args[0][0]), [step])

    def test_build_too_big_index(self, EngineMock):
        # Builder is mocked and steps are validated by it,
        # thus only test that the cli prints correct message
        engine = EngineMock.return_value
        builder = engine.create_builder.return_value
        builder.build.side_effect = IndexError(10) # from get_steps
        r = self.command_test("build --steps 10", config=HELLO_CONFIG, exit_code=1)
        builder.build.assert_called_once()
        self.assertListEqual(list(builder.build.call_args[0][0]), ['10'])
        self.assertIn("Index 10 is out of range.", r.err)

    def test_build_invalid_step(self, EngineMock):
        # Builder is mocked and steps are validated by it,
        # thus only test that the cli prints correct message
        engine = EngineMock.return_value
        builder = engine.create_builder.return_value
        builder.build.side_effect = KeyError('invalid') # from get_steps
        r = self.command_test("build --steps invalid", config=HELLO_CONFIG, exit_code=1)
        builder.build.assert_called_once()
        self.assertListEqual(list(builder.build.call_args[0][0]), ['invalid'])
        self.assertIn("No step named invalid.", r.err)


class TestInitAction(CliTestCase):

    def test_init(self):
        r1 = self.command_test('init', config=None)
        self.assertEqual(r1.out.strip(),
            "Project configuration file roman.yml created successfully.")
        self.assertIn('roman.yml', r1.files, msg="Project configuration file was not created!")
        data = r1.files['roman.yml'].get_written_content()
        self.assertIn('version:', data, msg="Project configuration seems to be invalid")

        r2 = self.command_test("init", config=data, exit_code=1)
        self.assertIn("A project configuration already exists at ", r2.err)
        self.assertIn('/roman.yml', r2.err)

    def test_init_recognizable_custom_file_with_ext(self):
        r = self.command_test('init', config_fn='roman.yaml')
        self.assertIn("Project configuration file", r.out)
        self.assertIn("created successfully.", r.out)
        self.assertNotIn("WARNING: roman won't recognize", r.err)
        self.assertNotIn("/roman.yaml as a project config file without the -f flag", r.err)
        self.assertIn('roman.yaml', r.files)

    def test_init_unrecognizable_custom_file_with_ext(self):
        r = self.command_test('init', config_fn='test_roman.yml')
        self.assertIn("Project configuration file", r.out)
        self.assertIn("created successfully.", r.out)
        self.assertIn("WARNING: roman won't recognize", r.err)
        self.assertIn("/test_roman.yml as a project config file without the -f flag", r.err)
        self.assertIn('test_roman.yml', r.files)

    def test_init_custom_file_without_ext(self):
        r = self.command_test("init", config_fn="test_roman")
        self.assertIn("Project configuration file", r.out)
        self.assertIn("created successfully.", r.out)
        self.assertIn("WARNING: roman won't recognize", r.err)
        self.assertIn("/test_roman as a project config file without the -f flag", r.err)
        self.assertIn('test_roman', r.files)


class TestConfigSetAction(CliTestCase):
    SETTINGS = "version: '1'"

    def test_normal_set(self):
        r = self.command_test("config -g set docker.timeout=100", settings=self.SETTINGS)
        self.assertEqual(r.out.strip(), "File successfully edited.")
        data = r.files[SETTINGS_FN].get_written_yaml()
        self.assertIn('docker', data)
        self.assertIn('timeout', data['docker'])
        self.assertEqual(data['docker']['timeout'], 100)

    def test_set_into_new_file(self):
        r = self.command_test("config -g set docker.timeout=100")
        self.assertEqual(r.out.strip(), "File created.")
        self.assertIn(SETTINGS_FN, r.files)
        data = r.files[SETTINGS_FN].get_written_yaml()
        self.assertIn('docker', data)
        self.assertIn('timeout', data['docker'])
        self.assertEqual(data['docker']['timeout'], 100)

    def test_set_wrong_type(self):
        r = self.command_test("config -g set docker.tls_verify=2", exit_code=1)
        self.assertEqual(
            "docker.tls_verify should be of type 'boolean', but was 'str'.", r.err.strip())
        r = self.command_test("config -g set docker.timeout=a", exit_code=1)
        self.assertEqual(
            "docker.timeout should be of type 'integer', but was 'str'.", r.err.strip())

    def test_set_not_selected(self):
        r = self.command_test("config -g -p set a=b", exit_code=1)
        self.assertEqual("Choose either global settings or project settings", r.err.strip())

    def test_set_wrong_format(self):
        r = self.command_test("config -g set docker.tls_verify: True", exit_code=1)
        self.assertEqual("Give values in format 'key=val'.", r.err.strip())


class TestConfigRemoveAction(CliTestCase):
    SETTINGS = {
        'version': '1.0',
        'docker': {'tls_verify': True}
    }

    def test_normal_rm(self):
        r = self.command_test("config -g remove docker.tls_verify", settings=self.SETTINGS)
        self.assertEqual("File successfully edited.", r.out.strip())

    def test_rm_empty_file(self):
        r = self.command_test("config -g remove docker.test")
        self.assertEqual(
            "Cannot delete from config because config file doesn't exist.", r.out.strip())

    def test_rm_nonexistant(self):
        r = self.command_test("config -g remove docker.test", settings=self.SETTINGS)
        self.assertIn("Key docker.test doesn't exist in config.", r.out)
        self.assertIn("No changes in the file.", r.out)

    def test_rm_config_not_selected(self):
        r = self.command_test("config -g -p remove a=b", exit_code=1)
        self.assertEqual("Choose either global settings or project settings", r.err.strip())


class TestStepListAction(CliTestCase):

    def test_step_list(self):
        config = dict(HELLO_CONFIG)
        config['steps'] = config['steps'] + [{'img': 'hei-maailma', 'name': 'moi'}]
        r = self.command_test("step list", config=config)
        self.assertIn("ID  NAME  IMAGE", r.out)
        self.assertIn(" 0. hello hello-world", r.out)
        self.assertIn(" 1. moi   hei-maailma", r.out)

    def test_step_list_empty(self):
        r = self.command_test("step list", config={'version': '2.0'})
        self.assertEqual("The project config has no steps.", r.out.strip())


class TestStepAddAction(CliTestCase):

    def test_step_add(self):
        r = self.command_test(
            "step add hello-world --name new_step "
            "--cmd 'make touchrst html' "
            "--env test1=a test2=${test1} --mnt /compile",
            config={'version': '2.0'}
        )
        self.assertEqual("Step successfully added to config.", r.out.strip())
        steps = r.files[CONFIG_FN].get_written_yaml()['steps']
        self.assertEqual(len(steps), 1)
        step = steps[0]
        self.assertEqual(step, {
            'img': 'hello-world',
            'name': 'new_step',
            'cmd': 'make touchrst html',
            'env': {
                'test1': 'a',
                'test2': '${test1}',
            },
            'mnt': '/compile'
        })

    def test_step_add_invalid_env(self):
        r = self.command_test("step add hello-world --env a: b", exit_code=1)
        self.assertEqual("env is a dict, so values need to be in key=val format, e.g. a=1 b=2",
            r.err.strip())

    def test_step_add_duplicate_name(self):
        r = self.command_test("step add hello-world --name hello",
            exit_code=1, config=HELLO_CONFIG)
        self.assertEqual("A step with the name 'hello' already exists.", r.err.strip())

    def test_step_add_validation_error(self):
        self.command_test("step add hello-world --name 123",
            config={'version': '2.0'}, exit_code=1)


class TestStepRemoveAction(CliTestCase):

    @patch('apluslms_roman.cli.input', create=True)
    def test_rm_action_confirm_no(self, mocked_input):
        mocked_input.side_effect = ['n']
        r = self.command_test("step rm hello", config=HELLO_CONFIG)
        config = r.files[CONFIG_FN]
        # if the file wasn't written, the file wasn't edited -> the step wasn't removed
        self.assertRaises(AssertionError, config.assert_called_with, abspath(CONFIG_FN), 'w')

    @patch('apluslms_roman.cli.input', create=True)
    def test_rm_action_confirm_yes(self, mocked_input):
        mocked_input.side_effect = ['y']
        # add step in order to ensure that all steps aren't deleted
        config = dict(HELLO_CONFIG)
        step = {'img': 'hello-world', 'name': 'step2'}
        config['steps'] = config['steps'] + [step]
        r = self.command_test("step rm hello", config=config)
        config = r.files[CONFIG_FN].get_written_yaml()
        self.assertIn('steps', config)
        steps = config['steps']
        self.assertIn(step, steps)
        step.update({'name': 'hello'})
        self.assertNotIn(step, steps)

    @patch('apluslms_roman.cli.input', create=True)
    def test_rm_action_force(self, mocked_input):
        mocked_input.side_effect = ['n']
        r = self.command_test("step rm -f hello", config=HELLO_CONFIG)
        config = r.files[CONFIG_FN].get_written_yaml()
        self.assertNotIn('steps', config)

    def test_rm_action_index_error(self):
        r = self.command_test("step rm -f 2", config=HELLO_CONFIG, exit_code=1)
        self.assertIn("Index is out of range", r.err)

    def test_rm_action_key_error(self):
        r = self.command_test("step rm -f hei", config=HELLO_CONFIG, exit_code=1)
        self.assertEqual("There is no step called 'hei'", r.err.strip())
