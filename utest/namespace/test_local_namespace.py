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
from utest.resources import datafilereader


class TestLocalNamespace(unittest.TestCase):

    def setUp(self):
        self._project = datafilereader.construct_project(datafilereader.SIMPLE_PROJECT)
        self._test = datafilereader.get_ctrl_by_name('Test Case', self._project.datafiles[0].tests)
        self._keyword = datafilereader.get_ctrl_by_name('Keyword', self._project.datafiles[0].keywords)
        print(self._keyword)

    def tearDown(self):
        self._project.close()

    def test_macro_controller_has_local_namespace(self):
        assert self._test.get_local_namespace() is not None
        assert self._keyword.get_local_namespace() is not None

    def test_keyword_argument_is_visible_in_keywords_local_namespace(self):
        assert self._keyword.get_local_namespace().has_name('${argument}')

    def test_keyword_argument_is_not_visible_in_test_cases_local_namespace(self):
        assert not self._test.get_local_namespace().has_name('${argument}')

    def test_keyword_steps_local_namespace_does_not_contain_local_variables_before_definition(self):
        for i in range(8):
            local_namespace = self._keyword.get_local_namespace_for_row(i)
            if i < 3:
                assert not local_namespace.has_name('${foo}')
            if i < 5:
                assert not local_namespace.has_name('${bar}')
            if i < 7:
                assert not local_namespace.has_name('${i}')

    def test_keyword_steps_local_namespace_does_contain_local_variables_after_definition(self):
        for i in range(9):
            local_namespace = self._keyword.get_local_namespace_for_row(i)
            assert local_namespace.has_name('${argument}')
            if i >= 3:
                assert local_namespace.has_name('${foo}')
            if i >= 5:
                assert local_namespace.has_name('${bar}')
            if i == 7 or i == 9:
                assert local_namespace.has_name('${i}')

    def test_keyword_steps_suggestions_with_local_variables(self):
        self._verify_suggestions_on_row(0, contains=['${argument}'], does_not_contain=['${foo}', '${bar}', '${i}'])
        self._verify_suggestions_on_row(3, contains=['${argument}', '${foo}'], does_not_contain=['${bar}', '${i}'])
        self._verify_suggestions_on_row(5, contains=['${argument}', '${foo}', '${bar}'], does_not_contain=['${i}'])
        self._verify_suggestions_on_row(7, contains=['${argument}', '${foo}', '${bar}', '${i}'])

    def test_suggestions_when_empty_text(self):
        self._verify_suggestions_on_row(4, start='', contains=['${argument}', '${foo}'], does_not_contain=['${bar}'])

    def test_suggestions_when_no_match(self):
        self._verify_suggestions_on_row(5, start='${no match}', does_not_contain=['${argument}', '${foo}', '${bar}'])

    def test_suggestions_when_only_part_matches(self):
        self._verify_suggestions_on_row(4, start='${f', contains=['${foo}'], does_not_contain=['${argument}', '${bar}'])
        self._verify_suggestions_on_row(4, start='fo', contains=['${foo}'], does_not_contain=['${argument}', '${bar}'])

    def _verify_suggestions_on_row(self, row, start='${', contains=None, does_not_contain=None):
        suggestion_names = [suggestion.name for suggestion in self._keyword.get_local_namespace_for_row(row).get_suggestions(start)]
        self.assertEqual(len(suggestion_names), len(set(suggestion_names)))
        if contains:
            for name in contains:
                if name not in suggestion_names:
                    raise AssertionError('Suggestions on row (%s) did not contain expected value "%s"' % (str(row), name))
        if does_not_contain:
            for name in does_not_contain:
                if name in suggestion_names:
                    raise AssertionError('Suggestions on row (%s) did contain illegal value "%s"' % (str(row), name))




if __name__ == '__main__':
    unittest.main()
