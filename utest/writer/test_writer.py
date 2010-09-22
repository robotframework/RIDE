import unittest

from robot.utils.asserts import assert_equals
from robotide.writer.writer import HtmlFileWriter


class Test(unittest.TestCase):

    def test_add_br_to_newlines(self):
        writer = HtmlFileWriter(None)
        repr = writer._add_br_to_newlines("""This is real new line:
        here we have a single backslash n: \\n and here backslash + newline: \\\n and here bslash blash n \\\\n and bslash x 3 n \\\\\\n """)
        assert_equals(repr, 'This is real new line:\n        here we have a single backslash n: \\n<br>\nand here backslash + newline: \\\n and here bslash blash n \\\\n and bslash x 3 n \\\\\\n<br>\n')

    def test_no_br_to_newlines_without_whitespace(self):
        writer = HtmlFileWriter(None)
        repr = writer._add_br_to_newlines(r"Here there is no space after backslash-n: '\n'")
        assert_equals(repr, r"Here there is no space after backslash-n: '\n'")

    def test_no_br_to_double_backslashes(self):
        writer = HtmlFileWriter(None)
        repr = writer._add_br_to_newlines(r"Here there is double backslash-n: \\n ")
        assert_equals(repr, r"Here there is double backslash-n: \\n ")


if __name__ == "__main__":
    unittest.main()