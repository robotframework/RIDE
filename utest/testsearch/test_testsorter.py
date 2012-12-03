#  Copyright 2008-2012 Nokia Siemens Networks Oyj
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
from testsearch.test_matcher import _TestSearchTest


class TestTestSorter(_TestSearchTest, unittest.TestCase):

    def test_exact_match_is_better_than_partial(self):
        self._matches_in_order('*exact*', ['aexact', 'exact', 'exact jotain', 'exact_foo', 'jotain exact', 'zexact'])

    def _matches_in_order(self, match_text, matches):
        match_objects = [self._match(match_text, name=name) for name in matches]
        for i in range(1, len(match_objects)):
            self._assert_is_greater(match_objects[i], match_objects[i-1])

    def test_name_is_better_than_doc(self):
        name_match = self._match('name', name='name')
        doc_match = self._match('doc', doc='doc')
        self._assert_is_greater(doc_match, name_match)

    def test_name_is_better_than_tag(self):
        name_match = self._match('name', name='name')
        tag_match = self._match('tag', tags=['tag'])
        self._assert_is_greater(tag_match, name_match)

    def test_tag_is_better_than_doc(self):
        tag_match = self._match('tag', tags=['tag'])
        doc_match = self._match('doc', doc='doc')
        self._assert_is_greater(doc_match, tag_match)

    def test_tags_order(self):
        tag1_match = self._match('*tag', tags=['atag'])
        tag2_match = self._match('*tag', tags=['btag'])
        self._assert_is_greater(tag2_match, tag1_match)

    def _assert_is_greater(self, greater, smaller):
        self.assertTrue(greater > smaller, msg='%r !>! %r' % (greater, smaller))
        self.assertFalse(smaller > greater)
        self.assertFalse(greater == smaller)


if __name__ == '__main__':
    unittest.main()
