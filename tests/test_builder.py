from unittest import TestCase

from apluslms_roman.builder import Builder
from apluslms_roman.configuration import ProjectConfig


class TestBuilderGetSteps(TestCase):

    def setUp(self):
        config = {
            'version': '2.0',
            'steps': [
                {'img': 'a', 'name': 'test1'},
                {'img': 'b', 'name': 'test2'},
                {'img': 'c'}
            ]}
        config = ProjectConfig(ProjectConfig.Container(
            '/a', allow_missing=True), None, config, None)
        self.builder = Builder(None, config)

    def test_withoutRefList(self):
        steps = self.builder.get_steps()
        self.assertEqual(len(steps), 3)
        names = [s.name for s in steps]
        self.assertEqual(names, ['test1', 'test2', None])

    def test_withDuplicateRef_shouldReturnStepOnce(self):
        steps = self.builder.get_steps(['test1', '0'])
        self.assertEqual(len(steps), 1)
        self.assertEqual(steps[0].name, 'test1')

    def test_namelessStep_refShouldBeIndex(self):
        steps = self.builder.get_steps(['2'])
        self.assertEqual(len(steps), 1)
        self.assertEqual(steps[0].ref, 2)


