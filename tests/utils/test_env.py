import re

from contextlib import ExitStack
from unittest import TestCase
from unittest.mock import patch

from apluslms_roman.builder import Builder
from apluslms_roman.configuration import ProjectConfig
from apluslms_roman.utils.env import (
    quoted_rgx,
    replacement_rgxs,
    sub_rgx,
    var_rgx,
    EnvDict
)
from apluslms_yamlidator.utils.collections import OrderedDict
from ..test_cli import CliTestCase


class TestRegexes(TestCase):

    def regex_test(self, matching, non_matching, regex):
        for var in matching:
            self.assertTrue(re.fullmatch(regex, var),
                msg="{} should match {}".format(var, regex))
        for var in non_matching:
            self.assertFalse(re.fullmatch(regex, var),
                msg="{} shouldn't match {}".format(var, regex))

    def test_varRegex(self):
        matching = ['${FOO}', '${foo}', '${FOO_BAR1}']
        non_matching = ['${1foo}', '${{.!-}']
        self.regex_test(matching, non_matching, var_rgx)

    def test_substitutionRegex(self):
        matching = ['${._?8$/}', '${foo:-bar}', '${foo:+bar}',]
        non_matching = ['${{}', '${}a']
        self.regex_test(matching, non_matching, sub_rgx)

    def test_quotedRegex(self):
        matching = ['"\'"', '\'"\'',]
        non_matching = ['a""', '"""', '\'"',]
        self.regex_test(matching, non_matching, quoted_rgx)

    def test_replacementRegexes(self):
        matching = ['a/b',]
        non_matching = ['a/b/c', '"a/b"/c']
        self.regex_test(matching, non_matching, replacement_rgxs[0])

        matching = ['"a//b"/"c/d"', '"a/b"/\'c/d\'']
        non_matching = ['"abc/e"', '"a/b"/c']
        self.regex_test(matching, non_matching, replacement_rgxs[1])

        matching = ['"a/b"/c']
        non_matching = ['"a/b"/"b/c"']
        self.regex_test(matching, non_matching, replacement_rgxs[2])

        matching = ['a/"b/c"']
        non_matching = ['"a/b"/"c/d"']
        self.regex_test(matching, non_matching, replacement_rgxs[3])


class TestVarExpansion(TestCase):

    def test_normal(self):
        env = EnvDict(([
            {'VAR': 'abc'},
            {'TEST': '${VAR}d'}
        ], 0)).get_combined()
        self.assertEqual({'VAR': 'abc', 'TEST': 'abcd'}, dict(env))

    def test_string(self):
        env = EnvDict((['a=b'], 0)).get_combined()
        self.assertEqual({'a': 'b'}, env)

    def test_nameAndValue(self):
        env = EnvDict(([{'name': 'a', 'value': 'b'}], 0)).get_combined()
        self.assertEqual({'a': 'b'}, env)

    def test_withNameAndUnset_shouldDeleteVarFromEnv(self):
        env = EnvDict(([
            {'name': 'a', 'value': 'b'},
            {'name': 'a', 'unset': 'true'}
        ], 0)).get_combined()
        self.assertEqual({}, env)

    def test_recursiveExpansion(self):
        env = EnvDict(([
            {'VAR': 'abc'},
            {'TEST1': '${VAR}'},
            {'TEST2': '${TEST1}'}
        ], 0)).get_combined()
        self.assertEqual({'VAR': 'abc', 'TEST1': 'abc', 'TEST2': 'abc'}, dict(env))

    def test_nestedExpansion(self):
        env = EnvDict(([
            {'VAR': 'hello'},
            {'TEST': '${VAR2:-${VAR}}!'},
        ], 0)).get_combined()
        self.assertEqual({'VAR': 'hello', 'TEST': 'hello!'}, dict(env))

    def test_nonStrExpansion_shouldNotTurnIntoStrings(self):
        env = EnvDict(([
            {'VAR': 1},
            {'LIST': ['a', '${VAR}2']},
            {'DICT': {'VAR': '${VAR}'}}
        ], 0)).get_combined()
        self.assertEqual({'VAR': 1, 'LIST': ['a', '12'], 'DICT': {'VAR': 1}}, dict(env))

    def test_expandSameName(self):
        env = EnvDict(([
            {'VAR': 'hello'},
            {'VAR': '${VAR}!'}
        ], 0)).get_combined()
        self.assertEqual({'VAR': 'hello!'}, dict(env))

    def test_shouldExpandInOrder(self):
        env = EnvDict(([
            {'VAR': 1},
            {'TEST1': '${VAR}'},
            {'VAR': 2},
            {'TEST2': '${VAR}'}
        ], 0)).get_combined()
        self.assertEqual({'VAR': 2, 'TEST1': 1, 'TEST2': 2}, dict(env))


class TestSubstitutionPatterns(TestCase):

    def test_defaultValue_shouldUseDefaultIfVarIsNull(self):
        env = EnvDict(([
            {'TEST1': '${VAR:-abc}'},
            {'TEST2': '${TEST1:-efg}'}
        ], 0)).get_combined()
        self.assertEqual({'TEST1': 'abc', 'TEST2': 'abc'}, dict(env))

    def test_altValue_shouldUseAltIfVarIsNotNull(self):
        env = EnvDict(([
            {'VAR': 'efg'},
            {'TEST1': '${VAR:+abc}'},
            {'TEST2': '${VAR2:+hij}'}
        ], 0),).get_combined()
        self.assertEqual({'VAR': 'efg', 'TEST1': 'abc', 'TEST2': ''}, dict(env))

    def test_replacement_shouldReplaceChars(self):
        tests = OrderedDict((
            ('VAR', ('aabbaa', 'aabbaa')),
            ('replace_one', ('${VAR/a/b}', 'babbaa')),
            ('replace_all', ('${VAR//a/c}', 'ccbbcc')),
            ('quoted1', ("${VAR/a/'a/b'}", 'a/babbaa')),
            ('quoted2', ('${quoted1/"a/b"/"b/b"}', 'b/babbaa')),
            ('quoted3', ('${quoted1/"a/"/b}', 'bbabbaa')),
            ('pattern1', ('${VAR/a+/c}', 'cbbaa')),
            ('pattern2', ('${VAR//(a|b)/c}', 'cccccc')),
            ('pattern3', ('${VAR/a*$/ccc}', 'aabbccc')),
            ('empty_replacement', ('${VAR//a/}', 'bb'))
        ))
        expanded = EnvDict((
            [{k: tests[k][0]} for k in tests],
        0)).get_combined()
        results = {k: tests[k][1] for k in tests}
        self.assertEqual(expanded, results)

    def test_expandList_shouldNotTurnIntoString(self):
        env = EnvDict(([
            {'LIST': ['a', 'b']},
            {'VAR': '${LIST}'}
        ], 0)).get_combined()
        self.assertEqual(env['VAR'], env['LIST'])


class TestExpansionErrors(TestCase):

    def check_err_msg(self, msg, func, *args):
        class EnvErr(Exception):
            pass

        with ExitStack() as ctx:
            error_mock = ctx.enter_context(patch(
                'apluslms_roman.utils.env.EnvDict._raise_err', side_effect=EnvErr))
            with self.assertRaises(EnvErr):
                func(*args)
            error_mock.assert_called_once()
            args = error_mock.call_args[0]
            self.assertIn(msg, str(args[0]))

    def test_selfReferring_shouldError(self):
        env = EnvDict(([{'TEST1': '${TEST1}'}], 0),)
        self.check_err_msg(
            "Variable TEST1 references itself",
            env.get_combined)

    def test_nonexistantVar_shouldError(self):
        env = EnvDict(([{'TEST2': '${TEST1}'}], 0))
        self.check_err_msg("TEST1 hasn't been defined", env.get_combined)

    def test_nonexistantReplacement_shouldError(self):
        env = EnvDict(([{'TEST2': '${TEST1/a/b}'}], 0),)
        self.check_err_msg("TEST1 hasn't been defined", env.get_combined)

    def test_unrecognizedPattern_shouldError(self):
        env = EnvDict(([{'VAR1': '${VAR%%test}'}], 0),)
        self.check_err_msg("Unrecognized parameter substitution pattern",
            env.get_combined)

    def test_wrongReplacementPattern_shouldError(self):
        env = EnvDict(([
            {'VAR': 'hello'},
            {'VAR1': '${VAR/e}'}], 0))
        self.check_err_msg("Wrong pattern replacement syntax", env.get_combined)


class TestCombineEnvs(TestCase):

    def test_combineEnvs(self):
        env = EnvDict(
            ([
                {'VAR1': 'test'},
                {'VAR2': 'hello'}
            ], 'a'),
            ([
                {'VAR2': '${VAR2}!'},
                {'VAR3': '${VAR1}2'}
            ], 'b'),
        ).get_combined()
        self.assertEqual(
            {'VAR1': 'test', 'VAR2': 'hello!', 'VAR3': 'test2'}, dict(env))


class TestLineCol(CliTestCase):

    def test_basic_shouldPrintCorrectPartOfYaml(self):
        config = {
            'version': '2',
            'steps': [{
                'img': 'hello',
                'name': 'hello',
                'env': [{'test1': '${test2}'}]
            }]
        }
        r = self.command_test('step env 0', config=config, exit_code=1)

        self.assertIn(
            "Invalid environment variable at index 0 in step hello (", r.err)
        self.assertIn("roman.yml", r.err)

        # 2 = indentation, 3 = indentation level, 1 = padding
        whitespace = 2 * 3 + 1
        # regex resembles something like
        # 3:   - test1: ${test2}
        #        ^ test2 hasn't been defined
        regex = (
            "[0-9]:" + " " * whitespace + "- test1: \${test2}\n" +
            " " * (whitespace + 4) + "\^ test2 hasn't been defined\n")
        self.assertRegex(r.err, regex)

    def test_list_shouldShowWholeList(self):
        settings = {
            'version': '1',
            'environment': [
                {'list': [
                    'a',
                    'b',
                    '${TEST1}'
                ]}
        ]}
        r = self.command_test('config env', config={'version': '2'},
            settings=settings, exit_code=1)
        whitespace = 2 * 1 + 1
        self.assertIn(
            ":" + " " * whitespace + "- list:\n" +
            " " * (whitespace + 4) + "^ TEST1 hasn't been defined", r.err
        )
        # check that ${TEST1} is visible in output
        self.assertIn("${TEST1}", r.err[r.err.index("^"):])

    def test_dict_shouldShowWholeDict(self):
        config = {
            'version': '2',
            'environment': [{
                'dict': OrderedDict((
                    ('a', 1),
                    ('b', 2),
                    ('c', '${TEST1}')
        ))}]}
        r = self.command_test('config env', config=config, exit_code=1)
        whitespace = 2 * 1 + 1
        self.assertIn(
            ":" + " " * whitespace + "- dict:\n" +
            " " * (whitespace + 4) + "^ TEST1 hasn't been defined", r.err
        )
        self.assertIn("${TEST1}", r.err[r.err.index("^"):])


class TestEditEnv(TestCase):

    def test_replacement_shouldDeleteAllOldValues(self):
        env = EnvDict(([{'name': 'a', 'unset': True}, 'a=b', {'a': 'c'}], 0))
        env.set_in_env(0, 'a', 1)
        env = env.get_env(0)
        self.assertEqual(['a=1'], env)


class TestStepEnvs(TestCase):

    # check that stuff from other steps doesn't
    # remain in the environment
    def test_withMultipleSteps_stepEnvsShouldNotAffectOtherSteps(self):
        config = {
            'version': '2.0',
            'steps': [
                {'img': 'a', 'env': [{'a': 'b'}]},
                {'img': 'b'}
            ]}
        config = ProjectConfig(ProjectConfig.Container(
            '/a', allow_missing=True), None, config, None)
        builder = Builder(None, config)
        steps = builder.get_steps()
        self.assertEqual(steps[0].env, {'a': 'b'})
        self.assertEqual(steps[1].env, {})
