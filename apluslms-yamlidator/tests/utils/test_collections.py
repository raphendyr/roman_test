import unittest

from apluslms_yamlidator.utils.collections import (
    Changes,
    ChangesDict,
    ChangesList,
)


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
