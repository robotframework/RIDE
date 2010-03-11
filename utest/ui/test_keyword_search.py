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

from robotide.ui.keywordsearch import _KeywordData
from robotide.namespace import ContentAssistItem

test_kws = [ContentAssistItem(name, source, desc) for name, source, desc in
            [ ('Should Be Equal', 'BuiltIn', 'Foo'),
              ('get bar', 'resource.txt', 'getting bar'),
              ('Get File', 'OperatingSystem', 'Bar'),
              ('User Keyword', 'resource.html', 'Quuz'), ]
           ]


class TestKeyWordData(unittest.TestCase):

    def test_sort_by_name(self):
        kw_data = _KeywordData(test_kws)
        for index, name in enumerate(['get bar',
                                      'Get File',
                                      'Should Be Equal',
                                      'User Keyword']):
            assert_equals(kw_data[index].name, name)

    def test_sort_by_name_reversed(self):
        kw_data = _KeywordData(test_kws, sort_up=False)
        for index, name in enumerate(['User Keyword',
                                      'Should Be Equal',
                                      'Get File', 
                                      'get bar']):
            assert_equals(kw_data[index].name, name)

    def test_sort_by_source(self):
        kw_data = _KeywordData(test_kws, 1)
        for index, name in enumerate(['Should Be Equal',
                                      'Get File',
                                      'User Keyword',
                                      'get bar']):
            assert_equals(kw_data[index].name, name)

    def test_sort_by_source_reversed(self):
        kw_data = _KeywordData(test_kws, 1, False)
        for index, name in enumerate(['get bar',
                                      'User Keyword',
                                      'Get File',
                                      'Should Be Equal']):
            assert_equals(kw_data[index].name, name)


if __name__ == "__main__":
    unittest.main()
