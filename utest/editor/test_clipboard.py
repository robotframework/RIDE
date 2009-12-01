import unittest

from robot.utils.asserts import assert_equals, assert_true, assert_false

from resources import PYAPP_REFERENCE #Needed to be able to create wx components
from robotide.editor.clipboard import GridClipboard


class TestGridClipBoard(unittest.TestCase):

    def test_with_string_content(self):
        self._test_clipboard('Hello, world!')

    def test_with_list_content(self):
        self._test_clipboard(['Hello', 'world!'])

    def test_with_dictionary_content(self):
        self._test_clipboard({0: 'Hello', 1: 'World!'})

    def _test_clipboard(self, content):
        clipb = GridClipboard()
        clipb.set_contents(content)
        assert_false(clipb.is_empty())
        assert_equals(clipb.get_contents(), content)


if __name__ == '__main__':
    unittest.main()
