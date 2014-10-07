import unittest
import hbml


class SimpleSourceTestCase(unittest.TestCase):
    def testSimpleSource(self):
        self.assertEqual(
            '''<div><h1></h1></div>''',
            hbml.compile((
                "%div\n"
                "  %h1"
            ))
        )


class TagAttrsTestCase(unittest.TestCase):
    def testSimpleAttr(self):
        self.assertEqual(
            '''<div id="yoyo" class="hello goodbye"></div>''',
            hbml.compile(
                "%div#yoyo.hello.goodbye"
            )
        )

    def testInBracketAttr(self):
        self.assertEqual(
            (
                '<div title="hello" data-id="2"'
                ' onclick="a = 1, b = 2, c = 3; item_clicked(a, b)"></div>'
            ),
            hbml.compile((
                '%div(title="hello", data-id="2",'
                ' onclick="a = 1, b = 2, c = 3; item_clicked(a, b)")'
            ))
        )

    def testExprAttr(self):
        self.assertEqual(
            '<div data-id="2"></div>',
            hbml.compile(
                '%div(data-id= 1 + 1)'
            )
        )

    def testExprAttrWithBrace(self):
        self.assertEqual(
            '<div data-id="HELLO"></div>',
            hbml.compile(
                '%div(data-id="hello".upper())'
            )
        )

    def testExprAttrWithMultiBraces(self):
        self.assertEqual(
            '<div data-id="45"></div>',
            hbml.compile(
                '%div(data-id= 3 * ( 1 + 2 * ( 3 + 4)))'
            )
        )

    def testNoTerminateTag(self):
        self.assertEqual(
            '<div data-id="2" data-name="hello"><h2></h2></div>',
            hbml.compile((
                "%div(data-id= 1 + 1,\n"
                "     data-name=\"hello\")\n"
                "  %h2"
            ))
        )


class TagTextTestCase(unittest.TestCase):
    def testSimpleText(self):
        self.assertEqual(
            '<div><h2>hello</h2></div>',
            hbml.compile((
                "%div\n"
                "  %h2 hello"
            ))
        )
