import os
import unittest

from nose.tools import assert_equals

# Needed to be able to create wx components
from resources import PYAPP_REFERENCE as _
from robotide.context import IS_WINDOWS
from robotide.editor.clipboard import _GridClipboard


if not IS_WINDOWS:
    class TestGridClipBoard(unittest.TestCase):

        def test_with_string_content(self):
            self._test_clipboard('Hello, world!', 'Hello, world!')

        def test_with_list_content(self):
            self._test_clipboard([['Hello', 'world!']], 'Hello\tworld!')

        def test_with_multiple_rows(self):
            self._test_clipboard([['Hello', 'world!'], ['Another', 'row']],
                                 'Hello\tworld!\nAnother\trow')

        def _test_clipboard(self, content, expected=''):
            clipb = _GridClipboard()
            clipb.set_contents(content)
            assert_equals(clipb._get_contents(),
                          expected.replace('\n', os.linesep))
