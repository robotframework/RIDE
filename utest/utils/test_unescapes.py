#  Copyright 2023-     Robot Framework Foundation
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
from robotide.utils import unescape_newlines_and_whitespaces

TEXT = 'This is the text to test.'
TEXT_MULTILINE = r"""This is the
\\n text
 to
\\   test

  
."""
TEXT_MULTILINE_ESCAPED = r"""This is\ the\r\\n text
 to\n\\ \  test\r
  \n."""
TEN_SPACES = ' ' * 10
TEN_SPACES_ESCAPED = TEN_SPACES.replace(' ', r'\ ')


class UnescapeTestCase(unittest.TestCase):

    @staticmethod
    def test_normal_string():
        result = unescape_newlines_and_whitespaces(TEXT)
        assert result == TEXT

    @staticmethod
    def test_spaces_string():
        result = unescape_newlines_and_whitespaces(TEN_SPACES_ESCAPED)
        assert result == TEN_SPACES

    @staticmethod
    def test_multiline_string():
        result = unescape_newlines_and_whitespaces(TEXT_MULTILINE_ESCAPED)
        assert result == TEXT_MULTILINE


if __name__ == "__main__":
    unittest.main()
