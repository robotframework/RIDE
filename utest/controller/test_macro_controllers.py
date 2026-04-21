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

from robotide.robotapi import TestCaseFile
from robotide.controller.filecontrollers import TestCaseFileController
from robotide.controller.macrocontrollers import (
    TestCaseController, UserKeywordController)
from robotide.controller.tablecontrollers import (
    TestCaseTableController, KeywordTableController)


class _BaseWithSteps(unittest.TestCase):

    def _test_copy_empty(self):
        for setting in self.ctrl.settings:
            assert not setting.is_set, 'not empty %s' % setting.__class__
        new = self.ctrl.copy('new name')
        for setting in new.settings:
            assert not setting.is_set, 'not empty %s' % setting.__class__

    def _test_copy_content(self):
        for setting in self.ctrl.settings:
            assert not setting.is_set, 'not empty %s' % setting.__class__
            setting.set_value('boo')
            setting.set_comment(['hobo'])
        new = self.ctrl.copy('new name')
        for setting in new.settings:
            assert setting.is_set, 'empty %s' % setting.__class__
            assert setting.value == 'boo', 'not boo %s' % setting.__class__
            assert setting.comment.as_list() == ['# hobo'], 'comment not copied %s' % setting.__class__


class TestCaseControllerTest(_BaseWithSteps):

    def setUp(self):
        self.tcf = TestCaseFile()
        self.testcase = self.tcf.testcase_table.add('Test')
        self.testcase.add_step(['Log', 'Hello'])
        self.testcase.add_step(['No Operation'])
        self.testcase.add_step(['Foo'])
        self.tcf.testcase_table.add('Another Test')
        tctablectrl = TestCaseTableController(TestCaseFileController(self.tcf),
                                              self.tcf.testcase_table)
        self.ctrl = TestCaseController(tctablectrl, self.testcase)

    def test_creation(self):
        for st in self.ctrl.settings:
            assert st is not None
        assert self.ctrl.datafile is self.tcf, self.ctrl.datafile

    def test_rename(self):
        self.ctrl.rename('Foo Barness')
        assert self.ctrl.name == 'Foo Barness'
        assert self.ctrl.dirty

    def test_rename_strips_whitespace(self):
        self.ctrl.rename('\t  \n Foo Barness        ')
        assert self.ctrl.name == 'Foo Barness'
        assert self.ctrl.dirty

    def test_copy_empty(self):
        self._test_copy_empty()

    def test_copy_content(self):
        self._test_copy_content()

    def test_add_tag(self):
        orig_num_tags = len(self.ctrl.tags.as_list())
        self.ctrl.add_tag('Some tag')
        assert len(self.ctrl.tags.as_list()) == orig_num_tags + 1


class UserKeywordControllerTest(_BaseWithSteps):

    def setUp(self):
        self.tcf = TestCaseFile()
        uk = self.tcf.keyword_table.add('UK')
        uk.add_step(['No Operation'])
        uk2 = self.tcf.keyword_table.add('UK 2')
        uk2.add_step(['No Operation'])
        uk3 = self.tcf.keyword_table.add('Open Browser')
        uk3.add_step(['No Operation'])
        uk4 = self.tcf.keyword_table.add('open file')
        uk4.add_step(['No Operation'])
        uk5 = self.tcf.keyword_table.add('CLOSE Application')
        uk5.add_step(['No Operation'])
        self.tablectrl = KeywordTableController(TestCaseFileController(self.tcf),
                                           self.tcf.keyword_table)
        self.ctrl = UserKeywordController(self.tablectrl, uk)
        self.ctrl2 = UserKeywordController(self.tablectrl, uk2)
        self.ctrl3 = UserKeywordController(self.tablectrl, uk3)
        self.ctrl4 = UserKeywordController(self.tablectrl, uk4)
        self.ctrl5 = UserKeywordController(self.tablectrl, uk5)

    def test_keyword_settings(self):
        labels = [setting.label for setting in self.ctrl.settings]
        assert 'Documentation' in labels
        assert 'Arguments' in labels
        assert 'Teardown' in labels
        assert 'Return Value' in labels
        assert 'Timeout' in labels

    def test_creation(self):
        for st in self.ctrl.settings:
            assert st is not None
        assert self.ctrl.steps[0].keyword == 'No Operation'
        assert self.ctrl.datafile is self.tcf

    def test_dirty(self):
        self.ctrl.mark_dirty()
        assert self.ctrl.dirty

    def test_move_up(self):
        assert not self.ctrl.move_up()
        self._assert_uk_in(0, 'UK')
        assert self.ctrl2.move_up()
        self._assert_uk_in(0, 'UK 2')

    def test_move_down(self):
        assert not self.ctrl5.move_down()
        self._assert_uk_in(4, 'CLOSE Application')
        assert self.ctrl.move_down()
        self._assert_uk_in(1, 'UK')
        self._assert_uk_in(0, 'UK 2')

    def test_delete(self):
        self.ctrl.delete()
        assert not 'UK' in self.tcf.keyword_table.keywords
        self._assert_uk_in(0, 'UK 2')

    def test_sort_case_sensitive(self):
        self._assert_uk_in(0, 'UK')
        self._assert_uk_in(1, 'UK 2')
        self._assert_uk_in(2, 'Open Browser')
        self._assert_uk_in(3, 'open file')
        self._assert_uk_in(4, 'CLOSE Application')
        index_list = self.tablectrl.sort()
        assert index_list == [2, 3, 1, 4, 0]
        print(f"DEBUG: test_sort_case_sensitive index={index_list[:]}")
        self._assert_uk_in(0, 'CLOSE Application')
        self._assert_uk_in(1, 'Open Browser')
        self._assert_uk_in(2, 'UK')
        self._assert_uk_in(3, 'UK 2')
        self._assert_uk_in(4, 'open file')


    def test_sort_case_insensitive(self):
        self._assert_uk_in(0, 'UK')
        self._assert_uk_in(1, 'UK 2')
        self._assert_uk_in(2, 'Open Browser')
        self._assert_uk_in(3, 'open file')
        self._assert_uk_in(4, 'CLOSE Application')
        index_list = self.tablectrl.sort(case_insensitive=True)
        assert index_list == [3, 4, 1, 2, 0]
        print(f"DEBUG: test_sort_case_sensitive index={index_list[:]}")
        self._assert_uk_in(0, 'CLOSE Application')
        self._assert_uk_in(1, 'Open Browser')
        self._assert_uk_in(2, 'open file')
        self._assert_uk_in(3, 'UK')
        self._assert_uk_in(4, 'UK 2')

    def _assert_uk_in(self, index, name):
        assert self.tcf.keyword_table.keywords[index].name == name

    def _assert_step(self, step, exp_assign=[], exp_keyword=None, exp_args=[]):
        assert step.assign == exp_assign
        assert step.keyword == exp_keyword
        assert step.args == exp_args

    def test_copy_empty(self):
        self._test_copy_empty()

    def test_copy_content(self):
        self._test_copy_content()


if __name__ == '__main__':
    unittest.main()

