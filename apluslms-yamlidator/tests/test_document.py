import unittest

from apluslms_yamlidator.document import find_ml, Document

from .test_validator import patch_validator_registry


class TestFindML(unittest.TestCase):

    def test_raises_keyerror_with_correct_key(self):
        data = {'foo': {}}
        with self.assertRaises(KeyError) as cm:
           find_ml(data, 'foo.bar.baz')
        self.assertEqual(cm.exception.args[0], 'foo.bar')


class TestInMemoryDocument(unittest.TestCase):

    def setUp(self):
        class TestDocument(Document):
            version = (1, 0)

        self.document = TestDocument.load('non-existent/file.yaml', allow_missing=True)

    def test_create_empty_document(self):
        d = self.document
        self.assertEqual(d.index, None)
        self.assertEqual(d.path, 'non-existent/file.yaml')
        self.assertIsNone(d.validator)
        d.validate() # nothing should happen

    def test_set_root_values_to_empty_document(self):
        d = self.document
        d['foo'] = 'bar'
        self.assertIn('foo', d)
        self.assertEqual(d['foo'], 'bar')

        d.setdefault('aa', 'aa')
        self.assertIn('aa', d)
        self.assertEqual(d['aa'], 'aa')

        self.assertSetEqual(set(d), {'foo', 'aa'})
        self.assertSetEqual(set(d.keys()), {'foo', 'aa'})
        self.assertSetEqual(set(d.items()), {('foo', 'bar'), ('aa', 'aa')})
        self.assertSetEqual(set(d.values()), {'bar', 'aa'})

        self.assertEqual(len(d), 2)

    def test_set_multilevel_values_to_empty_document(self):
        d = self.document
        d['foo'] = {}
        d['foo']['bar'] = 'baz'
        self.assertIn('foo', d)
        self.assertIn('bar', d['foo'])
        self.assertEqual(d['foo']['bar'], 'baz')

        d.mlset('aa.bb', 'cc')
        self.assertIn('aa', d)
        self.assertIn('bb', d['aa'])
        self.assertEqual(d['aa']['bb'], 'cc')
        self.assertEqual(d.mlget('aa.bb'), 'cc')

        d.mlsetwork('xx.yy', 'zz')
        self.assertIn('xx', d)
        self.assertIn('yy', d['xx'])
        self.assertEqual(d['xx']['yy'], 'zz')
        self.assertEqual(d.mlget('xx.yy'), 'zz')

        d.mlsetdefault('00.11', '22')
        self.assertIn('00', d)
        self.assertIn('11', d['00'])
        self.assertEqual(d['00']['11'], '22')
        self.assertEqual(d.mlget('00.11'), '22')


    def test_set_multilevel_value_to_document_with_default(self):
        d = self.document
        d.mlsetdefault('foo.bar', 'default')
        self.assertEqual(d.mlget('foo.bar'), 'default')
        d.mlset('foo.bar', 'real-value')
        self.assertEqual(d.mlget('foo.bar'), 'real-value')
        d.mlsetdefault('foo.bar', 'ignored-value')
        self.assertEqual(d.mlget('foo.bar'), 'real-value')

    def test_keyerror_raised_from_getitem_with_empty_document(self):
        d = self.document
        with self.assertRaises(KeyError):
            d['foo']
        with self.assertRaises(KeyError):
            d.mlget('foo.bar')
        with self.assertRaises(KeyError):
            d['foo']

        d['foo'] = {}
        with self.assertRaises(KeyError) as cm:
            d.mlget('foo.bar')
        self.assertEqual(cm.exception.args[0], 'foo.bar')
        with self.assertRaises(KeyError) as cm:
            d.mlget('foo.bar.baz')
        self.assertEqual(cm.exception.args[0], 'foo.bar.baz')

@patch_validator_registry
class TestInMemoryDocumentWithSchema(unittest.TestCase):

    def setUp(self):
        class TestDocument(Document):
            schema = 'test-base'
            version = (1, 0)

        self.document = TestDocument.load('non-existent/file.yaml', allow_missing=True)

    def test_validating_document(self, registry):
        self.document.mlset('foo.bar', 'baz')
        self.document.validate()

    def test_validating_document_with_only_defaults(self, registry):
        self.document.mlsetdefault('foo.bar', 'default')
        self.document.validate()

    def test_validating_invalid_document(self, registry):
        self.document.mlset('foo.bar', 100)
        with self.assertRaises(Exception): # FIXME: should be jsonschema.exceptions.ValidationError
            self.document.validate()
