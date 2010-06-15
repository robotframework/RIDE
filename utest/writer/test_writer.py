import unittest

from robot.utils.asserts import assert_equals
from robotide.writer.writer import HtmlFileWriter


class Test(unittest.TestCase):

    def test_add_br_to_newlines(self):
        writer = HtmlFileWriter(None)
        repr = writer._add_br_to_newlines("""This is real new line:
        here we have a single backslash n: \\n and here backslash + newline: \\\n and here bslash blash n \\\\n and bslash x 3 n \\\\\\n""")
        assert_equals(repr, 'This is real new line:\n        here we have a single backslash n: \\n<br>\n and here backslash + newline: \\\n and here bslash blash n \\\\n and bslash x 3 n \\\\\\n<br>\n')


if __name__ == "__main__":
    unittest.main()