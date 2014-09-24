import unittest
from hbml.compiler import Tag


class TagNameTestCase(unittest.TestCase):
    def testTagName(self):
        self.assertEqual(
            Tag('%div.hello').tag_name,
            'div'
        )

    def testDefaultTagName(self):
        self.assertEqual(
            Tag('.hello').tag_name,
            'div'
        )


class TagClassNamesTestCase(unittest.TestCase):
    def testClassNames(self):
        self.assertEqual(
            Tag('%div.hello').class_names,
            ['hello']
        )

    def testOnlyClassName(self):
        self.assertEqual(
            Tag('.hello').class_names,
            ['hello']
        )

    def testMultiClassNames(self):
        self.assertEqual(
            Tag('%div.hello.goodbye').class_names,
            ['hello', 'goodbye']
        )

    def testEmptyClassNames(self):
        self.assertEqual(
            Tag('%div').class_names,
            []
        )


class TagIdTestCase(unittest.TestCase):
    def testTagId(self):
        self.assertEqual(
            Tag('%div#hello').id,
            'hello'
        )

    def testOnlyTagId(self):
        self.assertEqual(
            Tag('#hello').id,
            'hello'
        )

    def testNoneTagId(self):
        self.assertEqual(
            Tag('%div').id,
            None
        )
