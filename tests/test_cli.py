import sys
from contextlib import contextmanager, ExitStack
from collections import namedtuple
from copy import deepcopy
from io import StringIO
from os.path import abspath, dirname, join
from shlex import split as shlex_split
from traceback import format_exc
from unittest import TestCase
from unittest.mock import patch, MagicMock

from apluslms_roman import cli
from apluslms_yamlidator.utils.yaml import rt_dump as yaml_dump
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
                config = yaml_dump(config)
            files[config_fn or CONFIG_FN] = config
        if config_fn:
            args.extend(('--file', config_fn))
        if settings:
            if not isinstance(settings, str):
                settings = yaml_dump(settings)
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
                        msg="cli.main exited with unexpect return code{}".format(
                            ": {}".format(exit_args[1]) if len(exit_args) == 2 else ""
                        ))

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

    def test_withNormalConfig(self):
        config = {'version': '2',
            'steps': [{'img': 'hello-world'}]}
        r = self.command_test('config', config=config)
        self.assertIn("---\n# roman settings", r.out)
        self.assertIn("---\n# project config", r.out)
        self.assertEqual(r.err, "")

    def test_withNoConfig_shouldError(self):
        r = self.command_test('config', config=None, exit_code=1)
        self.assertIn("Couldn't find project configuration from", r.err)
        self.assertIn("You can create a configuration file with", r.err)

    def test_withInvalidConfig_shouldError(self):
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

    def test_normalBuild(self, EngineMock):
        _ = self.command_test('build', config=HELLO_CONFIG)

        engine = EngineMock.return_value
        engine.create_builder.assert_called_once()
        builder_config = engine.create_builder.call_args[0][0]
        self.assertEqual(builder_config.steps[0]['img'], 'hello-world')

        builder = engine.create_builder.return_value
        builder.build.assert_called_once_with(step_refs=None, clean_build=False)

    def test_withEmptySteps_shouldSayNothingToBuild(self, EngineMock):
        r = self.command_test('build', config={'version': '2'}, exit_code=1)
        self.assertEqual(r.out.strip(), "Nothing to build.")

        engine = EngineMock.return_value
        engine.create_builder.assert_called_once()
        builder_config = engine.create_builder.call_args[0][0]
        self.assertEqual(len(builder_config.steps), 0)

        builder = engine.create_builder.return_value
        builder.build.assert_not_called()

    def test_withStepRefs_shouldCallBuildWithRefList(self, EngineMock):
        for step in ('hello', '0'):
            EngineMock.reset_mock()
            with self.subTest(step=step):
                self.command_test('build', '--steps', step, config=HELLO_CONFIG)

                engine = EngineMock.return_value
                builder = engine.create_builder.return_value
                builder.build.assert_called_once()
                self.assertListEqual(
                    list(builder.build.call_args.call_list()[0][1]['step_refs']),
                    [step])

    def test_withStepIdxOutOfRange_shouldError(self, EngineMock):
        # Builder is mocked and steps are validated by it,
        # thus only test that the cli prints correct message
        engine = EngineMock.return_value
        builder = engine.create_builder.return_value
        builder.build.side_effect = IndexError(10) # from get_steps
        r = self.command_test("build --steps 10", config=HELLO_CONFIG, exit_code=1)
        builder.build.assert_called_once()
        self.assertListEqual(
            list(builder.build.call_args.call_list()[0][1]['step_refs']),
            ['10'])
        self.assertIn("Index 10 is out of range.", r.err)

    def test_withNonexistantStepRef_shouldError(self, EngineMock):
        # Builder is mocked and steps are validated by it,
        # thus only test that the cli prints correct message
        engine = EngineMock.return_value
        builder = engine.create_builder.return_value
        builder.build.side_effect = KeyError('invalid') # from get_steps
        r = self.command_test("build --steps invalid", config=HELLO_CONFIG, exit_code=1)
        builder.build.assert_called_once()
        self.assertListEqual(
            list(builder.build.call_args.call_list()[0][1]['step_refs']),
            ['invalid'])
        self.assertIn("No step named invalid.", r.err)

    def test_withCleanFlag_shouldSetCleanBuildToTrue(self, EngineMock):
        engine = EngineMock.return_value
        builder = engine.create_builder.return_value
        r = self.command_test("build --clean", config=HELLO_CONFIG, exit_code=0)
        builder.build.assert_called_once_with(step_refs=None, clean_build=True)



class TestInitAction(CliTestCase):

    def test_normal(self):
        r1 = self.command_test('init', config=None)
        self.assertEqual(r1.out.strip(),
            "Project configuration file roman.yml created successfully.")
        self.assertIn('roman.yml', r1.files,
            msg="Project configuration file was not created!")
        data = r1.files['roman.yml'].get_written_content()
        self.assertIn('version:', data, msg="Project configuration seems to be invalid")

        r2 = self.command_test("init", config=data, exit_code=1)
        self.assertIn("A project configuration already exists at ", r2.err)
        self.assertIn('/roman.yml', r2.err)

    def test_withRecognizableCustomName_shouldNotWarnAboutName(self):
        r = self.command_test('init', config_fn='roman.yaml')
        self.assertIn("Project configuration file", r.out)
        self.assertIn("created successfully.", r.out)
        self.assertNotIn("WARNING: roman won't recognize", r.err)
        self.assertNotIn(
            "/roman.yaml as a project config file without the -f flag", r.err)
        self.assertIn('roman.yaml', r.files)

    def test_withUnrecognizableCustomName_shouldWarnAboutName(self):
        r = self.command_test('init', config_fn='test_roman.yml')
        self.assertIn("Project configuration file", r.out)
        self.assertIn("created successfully.", r.out)
        self.assertIn("WARNING: roman won't recognize", r.err)
        self.assertIn(
            "/test_roman.yml as a project config file without the -f flag", r.err)
        self.assertIn('test_roman.yml', r.files)

    def test_withNameWithoutExt_shouldWarnAboutName(self):
        r = self.command_test("init", config_fn="roman")
        self.assertIn("Project configuration file", r.out)
        self.assertIn("created successfully.", r.out)
        self.assertIn("WARNING: roman won't recognize", r.err)
        self.assertIn("/roman as a project config file without the -f flag", r.err)
        self.assertIn('roman', r.files)


class TestConfigEnv(CliTestCase):

    def test_printConfigEnv(self):
        config = {
            'version': '2.0',
            'environment': ['VAR=${VAR}!']
        }
        settings = {
            'version': '1.0',
            'environment': ['VAR=hello']
        }
        r = self.command_test("config env", config=config, settings=settings)
        self.assertEqual("VAR: hello!", r.out.strip())
        r = self.command_test("config -g env", config=config, settings=settings)
        self.assertEqual("VAR: hello", r.out.strip())

    def test_printStepEnv(self):
        config = deepcopy(HELLO_CONFIG)
        config['steps'][0]['env'] = [{'TEST': '${TEST}!'}]
        config['steps'].append({'img': 'hello-world', 'name': 'step2'})

        settings = {
            'version': '1.0',
            'environment': [{'TEST': 'hello'},]
        }

        r = self.command_test("step env 0", config=config, settings=settings)
        self.assertEqual("TEST: hello!", r.out.strip())
        r = self.command_test("step env step2", config=config, settings=settings)
        self.assertEqual("TEST: hello", r.out.strip())

    def test_addToEnv(self):
        r = self.command_test(
            "config env -a a=1",
            config={'version': '2.0'}
        )
        config = r.files[CONFIG_FN].get_written_yaml()
        self.assertEqual(['a=1'], config['environment'])

    def test_setInEnv(self):
        r = self.command_test(
            "config env -s a=1 -s b=2",
            config={
                'version': '2.0',
                'environment': [{'a': 'c'}, 'a=b']}
        )
        env = r.files[CONFIG_FN].get_written_yaml()['environment']
        self.assertEqual(['a=1', 'b=2'], env)

    def test_deleteFromEnv(self):
        r = self.command_test(
            "config env -d 0",
            config={
                'version': '2.0',
                'environment': ['a=1', 'b=2']}
        )
        env = r.files[CONFIG_FN].get_written_yaml()['environment']
        self.assertEqual(['b=2'], env)

    def test_deleteWithUnsetFlag_shouldMarkValueAsUnset(self):
        r = self.command_test(
            "config env --unset -d a",
            config={
                'version': '2.0',
                'environment': [{'b': 0}]}
        )
        env = r.files[CONFIG_FN].get_written_yaml()['environment']
        self.assertEqual([{'b': 0}, {'name': 'a', 'unset': True}], env)

    def test_deleteLastValueFromEnv_shouldDeleteEmptyEnv(self):
        r = self.command_test(
            "config env -d a",
            config={
                'version': '2.0',
                'environment': [{'a': 0}]}
        )
        config = r.files[CONFIG_FN].get_written_yaml()
        self.assertNotIn('environment', config)


class TestConfigSetAction(CliTestCase):
    SETTINGS = "version: '1'"

    def test_normal(self):
        r = self.command_test("config -g set docker.timeout=100", settings=self.SETTINGS)
        self.assertEqual(r.out.strip(), "File successfully edited.")
        data = r.files[SETTINGS_FN].get_written_yaml()
        self.assertIn('docker', data)
        self.assertIn('timeout', data['docker'])
        self.assertEqual(data['docker']['timeout'], 100)

    def test_withNewFile_shouldCreateFile(self):
        r = self.command_test("config -g set docker.timeout=100")
        self.assertEqual(r.out.strip(), "File created.")
        self.assertIn(SETTINGS_FN, r.files)
        data = r.files[SETTINGS_FN].get_written_yaml()
        self.assertIn('docker', data)
        self.assertIn('timeout', data['docker'])
        self.assertEqual(data['docker']['timeout'], 100)

    def test_withWrongType_shouldError(self):
        r = self.command_test("config -g set docker.tls_verify=2", exit_code=1)
        self.assertEqual(
            "docker.tls_verify should be of type 'boolean', but was 'str'.",
            r.err.strip())
        r = self.command_test("config -g set docker.timeout=a", exit_code=1)
        self.assertEqual(
            "docker.timeout should be of type 'integer', but was 'str'.", r.err.strip())

    def test_withLocalAndGlobalSeletcted_shouldError(self):
        r = self.command_test("config -g -p set a=b", exit_code=1)
        self.assertEqual("Choose either global settings or project settings",
            r.err.strip())

    def test_withWrongCommandSyntax_shouldError(self):
        r = self.command_test("config -g set docker.tls_verify: True", exit_code=1)
        self.assertEqual("Give values in format 'key=val'.", r.err.strip())


class TestConfigRemoveAction(CliTestCase):
    SETTINGS = {
        'version': '1.0',
        'docker': {'tls_verify': True}
    }

    def test_normal(self):
        r = self.command_test("config -g remove docker.tls_verify",
            settings=self.SETTINGS)
        self.assertEqual("File successfully edited.", r.out.strip())

    def test_withEmptyFile_shouldInformAboutEmptyFileAndNotError(self):
        r = self.command_test("config -g remove docker.test")
        self.assertEqual(
            "Cannot delete from config because config file doesn't exist.", r.out.strip())

    def test_withNonExistantKey_shouldNotChangeFile(self):
        r = self.command_test("config -g remove docker.test", settings=self.SETTINGS)
        self.assertIn("Key docker.test doesn't exist in config.", r.out)
        self.assertIn("No changes in the file.", r.out)

    def test_withLocalAndGlobalSelected_shouldError(self):
        r = self.command_test("config -g -p remove a=b", exit_code=1)
        self.assertEqual("Choose either global settings or project settings",
            r.err.strip())


class TestStepListAction(CliTestCase):

    def test_normal(self):
        config = dict(HELLO_CONFIG)
        config['steps'] = config['steps'] + [{'img': 'hei-maailma', 'name': 'moi'}]
        r = self.command_test("step list", config=config)
        self.assertEqual(
            "ID  NAME  IMAGE\n"
            " 0. hello hello-world\n"
            " 1. moi   hei-maailma\n", r.out)

    def test_withNoSteps_shouldSayThereAreNoSteps(self):
        r = self.command_test("step list", config={'version': '2.0'})
        self.assertEqual("The project config has no steps.", r.out.strip())

    def test_withQuestionMarkAsSteps_shouldPrintSteps(self):
        r = self.command_test("build -s ?", config=HELLO_CONFIG)
        self.assertIn('hello-world', r.out)


class TestStepAddAction(CliTestCase):

    def test_normal(self):
        r = self.command_test(
            "step add hello-world --name new_step "
            "--cmd 'make touchrst html' "
            "--env a=1 b=2 --mnt /compile",
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
            'env': ['a=1', 'b=2'],
            'mnt': '/compile'
        })

    def test_withInvalidEnv_shouldError(self):
        r = self.command_test("step add hello-world --env a: b", exit_code=1)
        self.assertEqual("Please give env values in 'key=var' format",
            r.err.strip())

    def test_withDuplicateName_shouldError(self):
        r = self.command_test("step add hello-world --name hello",
            exit_code=1, config=HELLO_CONFIG)
        self.assertEqual("A step with the name 'hello' already exists.", r.err.strip())

    def test_withInvalidValue_shouldError(self):
        self.command_test("step add hello-world --name 123",
            config={'version': '2.0'}, exit_code=1)


class TestStepRemoveAction(CliTestCase):

    @patch('apluslms_roman.cli.input', create=True)
    def test_withNoConfirm_shouldNotDelete(self, mocked_input):
        mocked_input.side_effect = ['n']
        r = self.command_test("step rm hello", config=HELLO_CONFIG)
        config = r.files[CONFIG_FN]
        # if the file wasn't written, the file wasn't edited -> the step wasn't removed
        self.assertRaises(AssertionError,
            config.assert_called_with, abspath(CONFIG_FN), 'w')

    @patch('apluslms_roman.cli.input', create=True)
    def test_withYesConfirm_shouldDelete(self, mocked_input):
        mocked_input.side_effect = ['y']
        config = deepcopy(HELLO_CONFIG)
        step = {'img': 'hello-world', 'name': 'step2'}
        config['steps'].append(step)
        r = self.command_test("step rm hello", config=config)
        config = r.files[CONFIG_FN].get_written_yaml()
        self.assertIn('steps', config)
        steps = config['steps']
        self.assertIn(step, steps)
        step.update({'name': 'hello'})
        self.assertNotIn(step, steps)

    @patch('apluslms_roman.cli.input', create=True)
    def test_withForce_shouldNotAskForConfirmation(self, mocked_input):
        mocked_input.side_effect = ['n']
        r = self.command_test("step rm -f hello", config=HELLO_CONFIG)
        config = r.files[CONFIG_FN].get_written_yaml()
        self.assertNotIn('steps', config)

    def test_withInvalidIndex_shouldError(self):
        r = self.command_test("step rm -f 2", config=HELLO_CONFIG, exit_code=1)
        self.assertIn("Index is out of range", r.err)

    def test_withInvalidName_shouldError(self):
        r = self.command_test("step rm -f hei", config=HELLO_CONFIG, exit_code=1)
        self.assertEqual("There is no step called 'hei'", r.err.strip())
