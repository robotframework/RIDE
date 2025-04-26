#  Copyright 2008-2015 Nokia Networks
#  Copyright 2016-     Robot Framework Foundation
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

import os
import pytest
# DISPLAY = os.getenv('DISPLAY')
# if not DISPLAY:
#     pytest.skip("Skipped because of missing DISPLAY", allow_module_level=True) # Avoid failing unit tests in system without X11
import unittest

from robotide.context import IS_WINDOWS
from robotide.editor.clipboard import _GridClipboard
from utest.resources import UIUnitTestBase

NEWLINE = '\n' if IS_WINDOWS else '\n'


class TestGridClipBoard(UIUnitTestBase):

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
        assert (clipb._get_contents() == expected)  # expected.replace('\n', os.linesep))


if __name__ == '__main__':
    unittest.main()

