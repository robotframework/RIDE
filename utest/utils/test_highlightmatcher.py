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

import unittest

from robotide.utils.highlightmatcher import highlight_matcher


class TestHighlightMatcher(unittest.TestCase):

    def test_empty_cell_should_not_match(self):
        assert not self.matcher('', '')

    def test_exact_match(self):
        assert self.matcher('My Keyword', 'My Keyword')
        assert not self.matcher('My Keyword', 'Keyword')

    def test_normalized_match(self):
        assert self.matcher('MyKeyword', 'My Keyword')
        assert self.matcher('mykeyword', 'My Keyword')
        assert self.matcher('my_key_word', 'My Keyword')

    def test_variable_with_equals_sign(self):
        assert self.matcher('${foo} =', '${foo}')
        assert self.matcher('${foo}=', '${foo}')
        assert self.matcher('${foo}=', '${  F O O }')
        assert not self.matcher('${foo}=', '${foo2}')

    def test_variable_inside_cell_content(self):
        assert self.matcher('${foo} =', 'some  ${foo} data')
        assert not self.matcher('some  ${foo} data', '${foo} =')
        assert not self.matcher('${foo}=', 'some not matching ${var}')
        assert self.matcher('${foo} =', 'Jep we have ${var} and ${foo}!')

    def test_list_variable(self):
        assert self.matcher('@{foo} =', '@{foo}')

    def test_list_variable_when_index_is_used(self):
        assert self.matcher('@{foo}[2]', '@{foo}')
        assert self.matcher('@{foo}[2]', '@{foo}[1]')
        assert self.matcher('@{foo}[2]', 'some @{foo} data')
        assert not self.matcher('@{foo}[2]', 'some @{foo2} data')
        assert not self.matcher('@{foo}123', '@{foo}')

    def test_extended_variable(self):
        assert self.matcher('${foo.extended}', '${foo}')
        assert self.matcher('${foo + 5}', '${foo}')
        assert self.matcher('${foo}', 'some ${foo.extended} data')
        assert self.matcher('${foo} =', 'some ${foo.extended} data')
        assert not self.matcher('${foo + 5}', '${foo2}')

    def test_list_variable_used_as_scalar(self):
        assert self.matcher('@{foo}', '${foo}')

    def matcher(self, value, content):
        return highlight_matcher(value, content)

if __name__ == "__main__":
    unittest.main()
