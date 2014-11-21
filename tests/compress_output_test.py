import unittest
import hbml


class CompressOutputTest(unittest.TestCase):
    def testDontCompress(self):
        self.assertEqual(
            '''<div><h1></h1></div>''',
            hbml.compile((
                "%div\n"
                "  %h1"
            ))
        )

        self.assertEqual(
            '<div>\n'
            '  <h1></h1>\n'
            '</div>\n',
            hbml.compile(
                (
                    "%div\n"
                    "  %h1"
                ),
                compress_output=False
            )
        )
