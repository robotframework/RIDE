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
from robot.parsing.model import TestCase, Tags
from robotide.controller.macrocontrollers import TestCaseController
from robotide.testsearch.testsearch import TestSearchMatcher


class TestTestSearchMatcher(unittest.TestCase):

    def setUp(self):
        self._matcher = TestSearchMatcher('name')

    def test_matching_name(self):
        self.assertTrue(self._matcher.matches(self._test('name')))

    def test_not_matching(self):
        self.assertFalse(self._matcher.matches(self._test('unknown', tags=['no match'], doc='no match')))

    def test_matching_name_partially(self):
        self.assertTrue(self._matcher.matches(self._test('prefix[name]postfix')))

    def test_matching_name_is_case_insensitive(self):
        self.assertTrue(self._matcher.matches(self._test('NamE')))

    def test_matching_to_documentation(self):
        self.assertTrue(self._matcher.matches(self._test('SOME', doc='There is some name')))

    def test_matching_to_tag(self):
        self.assertTrue(self._matcher.matches(self._test('SOME', tags=['name'])))

    def _test(self, name, tags=None, doc='documentation'):
        parent = lambda:0
        parent.datafile_controller = parent
        parent.register_for_namespace_updates = lambda *_:0
        parent.force_tags = []
        parent.default_tags = []
        robot_test = TestCase(parent=parent, name=name)
        robot_test.get_setter('documentation')(doc)
        robot_test.get_setter('tags')(tags or [])
        test = TestCaseController(parent, robot_test)
        return test


if __name__ == '__main__':
    unittest.main()
