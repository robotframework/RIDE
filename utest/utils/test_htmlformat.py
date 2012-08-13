import unittest
from robotide import utils

class HTMLFormatTestCase(unittest.TestCase):

    def test_formatting(self):
        formated = utils.html_format('| foo | bar |\n| zoo | zaa |\n\nhello')
        self.assertEqual('<table border="1">\n<tr>\n<td>foo</td>\n<td>bar</td>\n</tr>\n<tr>\n<td>zoo</td>\n<td>zaa</td>\n</tr>\n</table>\n<p>hello</p>', formated)

if __name__ == '__main__':
    unittest.main()
