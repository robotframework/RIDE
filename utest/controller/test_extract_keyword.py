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

from controller.base_command_test import *

from robotide.controller.ctrlcommands import ExtractKeyword, Undo
from robotide.publish.messages import RideUserKeywordAdded
from nose.tools import assert_true
from controller.controller_creator import FOR_LOOP_HEADER, FOR_LOOP_STEP2,\
    FOR_LOOP_STEP1


class TestExtractKeyword(TestCaseCommandTest):

    _namespace = None

    def setUp(self):
        TestCaseCommandTest.setUp(self)
        PUBLISHER.subscribe(self._on_keyword_added, RideUserKeywordAdded)

    def _on_keyword_added(self, message):
        self._new_keyword = message.item

    def test_extract(self):
        new_kw_name = 'New Keyword'
        self._exec(ExtractKeyword(new_kw_name, '', (0,1)))
        self._verify_step(0, new_kw_name)
        self._verify_step_number_change(-1)
        assert_true(self._ctrl.dirty)
        assert_equal(self._new_keyword.name, new_kw_name)

    def test_extract_with_for_loop(self):
        new_kw_name = 'New Keyword with For Loop'
        self._exec(ExtractKeyword(new_kw_name, '',
            (self._data_row(FOR_LOOP_HEADER),self._data_row(FOR_LOOP_STEP2))))
        self._verify_step(self._data_row(FOR_LOOP_HEADER), new_kw_name)
        self._verify_step_number_change(-2)
        assert_true(self._ctrl.dirty)
        assert_equal(self._new_keyword.name, new_kw_name)

    def not_implemented_test_undoing_extract(self):
        new_kw_name = 'New Keyword'
        self._exec(ExtractKeyword(new_kw_name, '', (0,1)))
        self._exec(Undo())
        self._verify_step_number_change(0)

    def not_implmented_test_extract_from_for_loop(self):
        new_kw_name = 'Flooo'
        self._exec(ExtractKeyword(new_kw_name, '',
            (self._data_row(FOR_LOOP_STEP1),self._data_row(FOR_LOOP_STEP2))))
        self._verify_step_number_change(-1)
        assert_true(self._ctrl.dirty)
        assert_equal(self._new_keyword.name, new_kw_name)
        assert_equal(self._steps[self._data_row(FOR_LOOP_STEP1)].as_list(), ['', new_kw_name])


if __name__ == "__main__":
    unittest.main()
