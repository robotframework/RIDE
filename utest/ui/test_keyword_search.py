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
from robotide.spec.iteminfo import ItemInfo

test_kws = [ItemInfo(name, source, desc) for name, source, desc in
            [ ('Should Be Equal', 'BuiltIn', 'Foo'),
              ('get bar', 'resource.txt', 'getting bar'),
              ('get bar2', 'resource2.txt', 'getting bar'),
              ('Get File', 'OperatingSystem', 'Bar'),
              ('Bar', 'OBarsystem', 'Doc'),
              ('BarBar', 'OBarBarSystem', 'Doc'),
              ('User Keyword', 'resource.html', 'Quuz'), ]
           ]


class TestKeyWordData(unittest.TestCase):

    def test_sort_by_search(self):
        kw_data = _KeywordData(test_kws, search_criteria='Bar')
        for index, name in enumerate(['Bar',
                                      'BarBar',
                                      'get bar',
                                      'get bar2',
                                      'Get File']):
            assert_equals(kw_data[index].name, name)

    def test_sort_by_name(self):
        kw_data = _KeywordData(test_kws)
        for index, name in enumerate(['Bar',
                                      'BarBar',
                                      'get bar',
                                      'get bar2',
                                      'Get File',
                                      'Should Be Equal',
                                      'User Keyword']):
            assert_equals(kw_data[index].name, name)

    def test_sort_by_name_reversed(self):
        kw_data = _KeywordData(test_kws, sort_up=False)
        for index, name in enumerate(['User Keyword',
                                      'Should Be Equal',
                                      'Get File',
                                      'get bar2', 
                                      'get bar',
                                      'BarBar',
                                      'Bar']):
            assert_equals(kw_data[index].name, name)

    def test_sort_by_source(self):
        kw_data = _KeywordData(test_kws, 1)
        for index, name in enumerate(['Should Be Equal',
                                      'BarBar',
                                      'Bar',
                                      'Get File',
                                      'User Keyword',
                                      'get bar',
                                      'get bar2']):
            assert_equals(kw_data[index].name, name)

    def test_sort_by_source_reversed(self):
        kw_data = _KeywordData(test_kws, 1, False)
        for index, name in enumerate(['get bar2',
                                      'get bar',
                                      'User Keyword',
                                      'Get File',
                                      'Bar',
                                      'BarBar',
                                      'Should Be Equal']):
            assert_equals(kw_data[index].name, name)


if __name__ == "__main__":
    unittest.main()
