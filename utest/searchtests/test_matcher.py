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

from robotide.robotapi import TestCase
from robotide.controller.macrocontrollers import TestCaseController
from robotide.searchtests.searchtests import TestSearchMatcher


class _TestSearchTest(object):

    def _test(self, name='name', tags=None, doc='documentation'):
        parent = lambda: 0
        parent.datafile_controller = parent
        parent.register_for_namespace_updates = lambda *_: 0
        parent.force_tags = []
        parent.default_tags = []
        parent.test_tags = []
        robot_test = TestCase(parent=parent, name=name)
        robot_test.get_setter('documentation')(doc)
        robot_test.get_setter('tags')(tags or [])
        test = TestCaseController(parent, robot_test)
        return test

    def _match(self, text, name='name', tags=None, doc='documentation'):
        return TestSearchMatcher(text).matches(self._test(name, tags, doc))


class TestTestSearchMatcher(_TestSearchTest, unittest.TestCase):

    def test_matching_name(self):
        assert self._match('name', name='name')

    def test_not_matching(self):
        assert not self._match('tERm', name='no match',
                                 tags=['no match'], doc='no match')

    def test_matching_name_partially(self):
        assert self._match('match', doc='prefix[match]postfix')

    def test_matching_name_is_case_insensitive_in_tags(self):
        assert self._match('mAtCh', tags=['MATcH'])

    def test_matching_name_is_case_insensitive_in_name(self):
        assert self._match('mAtCh', name=' MATcH')

    def test_matching_name_is_case_insensitive_in_doc(self):
        assert self._match('mAtCh', doc='Doc MATcHoc')

    def test_matching_to_documentation(self):
        assert self._match('docstring', doc='docstring matching!')

    def test_matching_to_tag(self):
        assert self._match('tag', tags=['tag'])

    def test_multiple_match_terms(self):
        assert self._match('name tag doc', name='name!',
                                tags=['foo', 'tag', 'bar'],
                                doc='well doc to you!')

if __name__ == "__main__":
    unittest.main()
