import unittest
import hbml


class StringExprTestCase(unittest.TestCase):
    def testStringEscape(self):
        self.assertEqual(
            r'<a onclick="alert(\"hello\")">yoyo</a>',
            hbml.compile(
                r'%a(onclick="alert(\"hello\")") yoyo'
            )
        )

    def testStringEscapeAtLast(self):
        self.assertEqual(
            r'<div title="h\""></div>',
            hbml.compile(
                r'%div(title="h\"")'
            )
        )

    def testMultiAttrStringEscape(self):
        self.assertEqual(
            r'<a onclick="alert(\"hello\")" href="#">yoyo</a>',
            hbml.compile(
                r'%a(onclick="alert(\"hello\")", href="#") yoyo'
            )
        )
