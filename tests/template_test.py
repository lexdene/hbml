import os
import unittest
import hbml


def _file_content(path):
    with open(path, 'r') as f:
        content = f.read()

    return content


DIRPATH = os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    'templates'
)


class TemplateTestCase(unittest.TestCase):
    def _test_file(self, filename):
        self.assertEqual(
            _file_content(
                os.path.join(
                    DIRPATH,
                    filename + '.html'
                )
            ),
            hbml.compile(
                _file_content(
                    os.path.join(
                        DIRPATH,
                        filename + '.hbml'
                    )
                )
            ) + "\n"
        )

    def _test_uncompress_file(self, filename):
        self.assertEqual(
            _file_content(
                os.path.join(
                    DIRPATH,
                    filename + '.uncompress.html'
                )
            ),
            hbml.compile(
                _file_content(
                    os.path.join(
                        DIRPATH,
                        filename + '.hbml'
                    )
                ),
                compress_output=False
            )
        )

    def testTemplates(self):
        for filename in os.listdir(DIRPATH):
            filename, extname = os.path.splitext(filename)

            if extname == '.hbml':
                with self.subTest(filename=filename):
                    self._test_file(filename)
                    self._test_uncompress_file(filename)
