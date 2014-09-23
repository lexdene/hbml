import unittest
from functools import lru_cache


class Bar(object):
    def __init__(self, data):
        self.__data = data
        self.__call_count = 0

    @property
    @lru_cache(maxsize=None)
    def data(self):
        self.__call_count += 1
        return self.__data

    @property
    def call_count(self):
        return self.__call_count


class LruCacheTestCase(unittest.TestCase):
    def testLruCache(self):
        a = Bar(1)
        self.assertEqual(
            1,
            a.data
        )
        self.assertEqual(
            1,
            a.data
        )
        self.assertEqual(
            1,
            a.data
        )
        self.assertEqual(
            1,
            a.data
        )
        self.assertEqual(
            1,
            a.data
        )
        self.assertEqual(
            1,
            a.call_count
        )

        b = Bar(2)
        self.assertEqual(
            2,
            b.data
        )
        self.assertEqual(
            2,
            b.data
        )
        self.assertEqual(
            2,
            b.data
        )
        self.assertEqual(
            2,
            b.data
        )
        self.assertEqual(
            2,
            b.data
        )
        self.assertEqual(
            2,
            b.data
        )
        self.assertEqual(
            1,
            b.call_count
        )
