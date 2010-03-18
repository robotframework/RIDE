#  Copyright 2008 Nokia Siemens Networks Oyj
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

import unittest

from robot.utils.asserts import assert_equals

from resources import PYAPP_REFERENCE as _ #Needed to be able to create wx components
from robotide.editor.clipboard import _GridClipboard


class TestGridClipBoard(unittest.TestCase):

    def test_with_string_content(self):
        self._test_clipboard('Hello, world!')

    def test_with_list_content(self):
        self._test_clipboard(['Hello', 'world!'])

    def test_with_dictionary_content(self):
        self._test_clipboard({0: 'Hello', 1: 'World!'})

    def test_tab_and_newline_separated_string_is_returned_as_grid_data(self):
        self._test_clipboard('Hello\tWorld\nAnd\tgreetings\tsir!',
                             [['Hello', 'World'], ['And', 'greetings', 'sir!']])

    def _test_clipboard(self, content, expected=None):
        clipb = _GridClipboard()
        clipb.set_contents(content)
        assert_equals(clipb.get_contents(), expected or content)


if __name__ == '__main__':
    unittest.main()
