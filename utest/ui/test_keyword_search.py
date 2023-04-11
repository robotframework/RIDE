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

from robotide.ui.keywordsearch import _KeywordData, _SearchCriteria,\
    ALL_KEYWORDS, ALL_USER_KEYWORDS, ALL_LIBRARY_KEYWORDS, _SortOrder
from robotide.spec.iteminfo import ItemInfo

test_kws = [ItemInfo(name, source, desc) for name, source, desc in
            [('Should Be Equal', 'BuiltIn', 'Foo'),
             ('get bar', 'resource.robot', 'getting bar'),
             ('get bar2', 'resource2.robot', 'getting bar'),
             ('Get File', 'OperatingSystem', 'Bar'),
             ('Bar', 'OBarsystem', 'Doc'),
             ('BarBar', 'OBarBarSystem', 'Doc'),
             ('User Keyword', 'resource.resource', 'Quuz'), ]
            ]


class Keyword(object):

    def __init__(self, name, source, doc):
        self.name = name
        self.source = source
        self.doc = doc

    def is_user_keyword(self):
        return self.source.endswith('.robot')

    def is_library_keyword(self):
        return not self.source.endswith('.robot')


class TestSearchCriteria(unittest.TestCase):
    keyword = Keyword('start Da ta end', 'source.robot', 'some dO c here')
    library_keyword = Keyword('start Da ta end', 'library', 'some dO c here')

    def test_defaults(self):
        criteria = _SearchCriteria()
        for kw in test_kws:
            assert criteria.matches(kw)

    def test_pattern(self):
        self._test_criteria(True, 'data', False, self.keyword)
        self._test_criteria(False, 'no match', False, self.keyword)

    def test_doc_search(self):
        self._test_criteria(True, 'doc', True, self.keyword)
        self._test_criteria(False, 'doc', False, self.keyword)

    def test_exact_source_filter_matches(self):
        self._test_criteria(True, '', True, self.keyword, 'source.robot')
        self._test_criteria(True, 'data', True, self.keyword, 'source.robot')
        self._test_criteria(
            False, 'no match', True, self.keyword, 'source.robot')

    def test_exact_source_filter_does_not_match(self):
        self._test_criteria(False, 'doc', True, self.keyword, 'Some')
        self._test_criteria(False, 'data', False, self.keyword, 'Some')

    def test_source_filter_all_keywords(self):
        self._test_criteria(True, '', True, self.keyword, ALL_KEYWORDS)
        self._test_criteria(True, '', True, self.library_keyword, ALL_KEYWORDS)

    def test_source_filter_resource_keywords(self):
        self._test_criteria(True, '', True, self.keyword, ALL_USER_KEYWORDS)
        self._test_criteria(
            False, '', True, self.library_keyword, ALL_USER_KEYWORDS)

    def test_source_filter_library_keywords(self):
        self._test_criteria(
            True, '', True, self.library_keyword, ALL_LIBRARY_KEYWORDS)
        self._test_criteria(
            False, '', True, self.keyword, ALL_LIBRARY_KEYWORDS)

    def _test_criteria(self, expected, pattern, search_doc, keyword,
                       source_filter=ALL_KEYWORDS):
        criteria = _SearchCriteria(pattern, search_doc, source_filter)
        assert criteria.matches(keyword) == expected


class TestKeyWordData(unittest.TestCase):

    def test_sort_by_search(self):
        order = _SortOrder()
        order.searched('Bar')
        kw_data = _KeywordData(test_kws, order, search_criteria='Bar')
        for index, name in enumerate(['Bar',
                                      'BarBar',
                                      'get bar',
                                      'get bar2',
                                      'Get File']):
            assert kw_data[index].name == name

    def test_sort_by_name(self):
        order = _SortOrder()
        kw_data = _KeywordData(test_kws, order)
        for index, name in enumerate(['Bar',
                                      'BarBar',
                                      'get bar',
                                      'get bar2',
                                      'Get File',
                                      'Should Be Equal',
                                      'User Keyword']):
            assert kw_data[index].name == name

    def test_sort_by_name_reversed(self):
        order = _SortOrder()
        order.sort(0)
        kw_data = _KeywordData(test_kws, order)
        for index, name in enumerate(['User Keyword',
                                      'Should Be Equal',
                                      'Get File',
                                      'get bar2',
                                      'get bar',
                                      'BarBar',
                                      'Bar']):
            assert kw_data[index].name == name

    def test_sort_by_source(self):
        order = _SortOrder()
        order.sort(1)
        kw_data = _KeywordData(test_kws, order)
        for index, name in enumerate(['Should Be Equal',
                                      'BarBar',
                                      'Bar',
                                      'Get File',
                                      'User Keyword',
                                      'get bar',
                                      'get bar2']):
            assert kw_data[index].name == name

    def test_sort_by_source_reversed(self):
        order = _SortOrder()
        order.sort(1)
        order.sort(1)
        kw_data = _KeywordData(test_kws, order)
        for index, name in enumerate(['get bar2',
                                      'get bar',
                                      'User Keyword',
                                      'Get File',
                                      'Bar',
                                      'BarBar',
                                      'Should Be Equal']):
            assert kw_data[index].name == name


if __name__ == "__main__":
    unittest.main()
