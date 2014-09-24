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
            hbml.compile((
                "%div#yoyo.hello.goodbye"
            ))
        )
