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
