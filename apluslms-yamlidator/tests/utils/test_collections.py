import unittest

from apluslms_yamlidator.utils.collections import (
    recursive_update,
    Changes,
    ChangesDict,
    ChangesList,
)


class TestRecursiveUpdate(unittest.TestCase):

    def test_overwrites_old_values(self):
        old = {
            'a': 1,
            'b': 'abc'
        }
        new = {
            'a': 2,
            'b': 'xyz'
        }
        recursive_update(old, new)
        self.assertEqual(old, new)

    def test_writes_new_keys_and_keeps_old(self):
        old = {'a': 1}
        new = {
            'b': 2
        }
        recursive_update(old, new)
        self.assertIn('a', old)
        self.assertIn('b', old)

    def test_extends_lists(self):
        old = {
            'list1': [1,2,3],
            'list2': ['a','b']
        }
        new = {
            'list1': [4,5,6],
            'list2': ('c','d')
        }
        recursive_update(old, new)
        self.assertEqual(old['list1'], [1,2,3,4,5,6])
        self.assertEqual(old['list2'], ['a','b','c','d'])

    def test_updates_dicts(self):
        old = {'dict': {
            'a': 1,
            'b': 2
        }}
        new = {'dict': {
            'a': 3,
            'c': 1
        }}
        recursive_update(old, new)
        self.assertEqual(old['dict']['a'], 3)
        self.assertEqual(old['dict']['b'], 2)
        self.assertEqual(old['dict']['c'], 1)

    def test_updates_dicts_recursive(self):
        old = {'dict1': {'dict2': {'foo': 'bar'}}}
        new = {'dict1': {'dict2': {'a': 1}, 'dict3': {'b': 2}}}
        recursive_update(old, new)
        self.assertEqual(sorted(list(old['dict1'].keys())), sorted(['dict2', 'dict3']))
        self.assertEqual(old['dict1']['dict2'], {'foo': 'bar', 'a': 1})


class TestChanges(unittest.TestCase):

    def test_wrap_list(self):
        l = [1, 2, 3]
        c = Changes.wrap(l)
        self.assertListEqual(c.get_data(), l)
        self.assertListEqual(list(c), l)

    def test_wrap_dict(self):
        d = {'a': 'b'}
        c = Changes.wrap(d)
        self.assertDictEqual(c.get_data(), d)
        self.assertDictEqual(dict(c), d)


class TestChangesDict(unittest.TestCase):

    def test_wrap_dict(self):
        d = ChangesDict({'foo': 'bar'})
        self.assertEqual(d.get_data()['foo'], 'bar')

    def test_add_data_get_data(self):
        d = ChangesDict({})
        d['foo'] = 'bar'
        self.assertEqual(d.get_data()['foo'], 'bar')

    def test_contains_and_keys(self):
        d = ChangesDict({'a': 'a'})
        self.assertEqual(len(d), 1)

        d['b'] = 'b'
        self.assertEqual(len(d), 2)

        d.setdefault('c', 'c')
        self.assertEqual(len(d), 3)

        d.setwork('d', 'd')
        self.assertEqual(len(d), 4)

        keys = ('a', 'b', 'c', 'd')
        self.assertSetEqual(set(keys), set(d.keys()))

        for key in keys:
            with self.subTest(key=key):
                self.assertIn(key, d)
                self.assertIn(key, d.keys())


    def test_setitem_then_setdefault(self):
        d = ChangesDict({})
        d.setdefault('foo', 'default')
        self.assertEqual(d['foo'], 'default')
        d['foo'] = 'bar'
        self.assertEqual(d['foo'], 'bar')
        d.setdefault('foo', 'not-used')
        self.assertEqual(d['foo'], 'bar')


class TestChangesList(unittest.TestCase):

    def test_wrap_list(self):
        d = ChangesList([1, 2, 3])
        self.assertListEqual(d.get_data(), [1, 2, 3])

    # TODO: add more tests for the list
