import unittest
from unittest.mock import patch

from apluslms_yamlidator.utils.collections import Changes
from apluslms_yamlidator.validator import Validator


test_schemas = [
    {
        '$id': 'test-base-v1.0',
        '$schema': 'http://json-schema.org/draft-04/schema',
        'type': 'object',
        'additionalProperties': False,
        'properties': {
            'version': {
                'type': 'string',
             },
            'foo': {
                'type': 'object',
                'additionalProperties': False,
                'properties': {
                    'bar': {
                        'type': 'string',
                    },
                },
            },
        },
    },
]


def get_test_schemas(*args, **kwargs):
    return {schema['$id']: (lambda: schema) for schema in test_schemas}


patch_validator_registry = patch('apluslms_yamlidator.validator.schema_registry', **{
    'schemas_with_dirs.side_effect': get_test_schemas,
    'find_file': None,
})


@patch_validator_registry
class TestValidator(unittest.TestCase):

    def setUp(self):
        super().setUp()
        self.validator = Validator()

    def test_data_with_schema(self, registry):
        def val(data):
            return self.validator.validate(data, schema_name='test-base', major=1)

        # some valid datas
        self.assertTrue(val({}))
        self.assertTrue(val({'foo': {}}))
        self.assertTrue(val({'foo': {'bar': 'baz'}}))

        # some invalid datas
        self.assertFalse(val('invalid'))
        self.assertFalse(val({'foo': 'invalid'}))
        self.assertFalse(val({'foo': {'bar': 0}}))
        self.assertFalse(val({'foo': {'invalid': 'invalid'}}))

    def test_changesdict_with_schema(self, registry):
        def val(data):
            data = Changes.wrap(data)
            return self.validator.validate(data, schema_name='test-base', major=1)

        # some valid datas
        self.assertTrue(val({}))
        self.assertTrue(val({'foo': {}}))
        self.assertTrue(val({'foo': {'bar': 'baz'}}))

        # some invalid datas
        with self.assertLogs('apluslms_yamlidator.validator', 'WARNING'):
            self.assertFalse(val({'foo': 'invalid'}))
        with self.assertLogs('apluslms_yamlidator.validator', 'WARNING'):
            self.assertFalse(val({'foo': {'bar': 0}}))
        with self.assertLogs('apluslms_yamlidator.validator', 'WARNING'):
            self.assertFalse(val({'foo': {'invalid': 'invalid'}}))
