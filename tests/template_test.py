import os
import unittest
import hbml


def _file_content(path):
    with open(path, 'r') as f:
        content = f.read()

    return content


class TemplateTestCase(unittest.TestCase):
    def testTemplates(self):
        dirpath = os.path.join(
            os.path.dirname(os.path.realpath(__file__)),
            'templates'
        )

        for filename in os.listdir(dirpath):
            filename, extname = os.path.splitext(filename)

            if extname == '.hbml':
                with self.subTest(filename=filename):
                    self.assertEqual(
                        _file_content(
                            os.path.join(
                                dirpath,
                                filename + '.html'
                            )
                        ),
                        hbml.compile(
                            _file_content(
                                os.path.join(
                                    dirpath,
                                    filename + '.hbml'
                                )
                            )
                        ) + "\n"
                    )
