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

import os
import pytest
# DISPLAY = os.getenv('DISPLAY')
# if not DISPLAY:
#     pytest.skip("Skipped because of missing DISPLAY", allow_module_level=True) # Avoid failing unit tests in system without X11
import wx
import unittest
from robotide.controller.filecontrollers import TestCaseFileController
from robotide.editor.editordialogs import (
    TestCaseNameDialog, UserKeywordNameDialog)
from robotide.validators import TestCaseNameValidator, UserKeywordNameValidator, ArgumentsValidator
from robotide.robotapi import TestCaseFile
from utest.resources import UIUnitTestBase


def file_controller():
    return TestCaseFileController(TestCaseFile())


def get_dlg_validators(dlg):
    return [_._editor.GetValidator() for _ in dlg._get_editors(None)]


class TestNameDialogTest(UIUnitTestBase):

    def test_get_name_item_is_noe(self):
        test_ctrl = file_controller().create_test('A test')
        dlg = TestCaseNameDialog(test_ctrl)
        assert dlg.get_name() == ''

    def test_get_name_item_is_not_none(self):
        test_ctrl = file_controller().create_test('A test')
        dlg = TestCaseNameDialog(test_ctrl, item=test_ctrl.data)
        assert dlg.get_name() == 'A test'

    def test_execute(self):
        test_ctrl = file_controller().create_test('A test')
        dlg = TestCaseNameDialog(test_ctrl, item=test_ctrl.data)
        wx.CallAfter(dlg.EndModal, wx.ID_YES)
        assert dlg.execute() == None

    def test_get_title(self):
        test_ctrl = file_controller().create_test('A test')
        dlg = TestCaseNameDialog(test_ctrl, item=test_ctrl.data)
        assert dlg.GetTitle() == 'New Test Case'

    def test_validators(self):
        test_ctrl = file_controller().create_test('A test')
        dlg = TestCaseNameDialog(test_ctrl, item=test_ctrl.data)
        assert len(get_dlg_validators(dlg)) == 1

    def test_case_validator(self):
        test_ctrl = file_controller().create_test('A test')
        dlg = TestCaseNameDialog(test_ctrl, item=test_ctrl.data)
        validator = get_dlg_validators(dlg)[0]
        assert isinstance(validator, TestCaseNameValidator)


class TestUserKeywordNameDialog(UIUnitTestBase):

    def test_get_name_item_is_none(self):
        kw_ctrl = file_controller().create_keyword('Keyword it is')
        dlg = UserKeywordNameDialog(kw_ctrl)
        assert dlg.get_name() == ''

    def test_get_name_item_is_not_none(self):
        kw_ctrl = file_controller().create_keyword('Keyword it is')
        dlg = UserKeywordNameDialog(kw_ctrl, item=kw_ctrl.data)
        assert dlg.get_name() == 'Keyword it is'

    def test_get_args_item_is_none(self):
        kw_ctrl = file_controller().create_keyword('Keyword it is', '${a1} | ${a2}')
        dlg = UserKeywordNameDialog(kw_ctrl)
        assert dlg.get_args() == ''

    def test_get_args_item_is_not_none(self):
        kw_ctrl = file_controller().create_keyword('Keyword it is', '${a1} | ${a2}')
        dlg = UserKeywordNameDialog(kw_ctrl, item=kw_ctrl.data)
        assert dlg.get_args() == '${a1} | ${a2}'

    def test_get_empty_args(self):
        kw_ctrl = file_controller().create_keyword('Keyword it is')
        dlg = UserKeywordNameDialog(kw_ctrl, item=kw_ctrl.data)
        assert dlg.get_args() == ''

    def test_execute(self):
        kw_ctrl = file_controller().create_keyword('Keyword it is', '${a1} | ${a2}')
        dlg = UserKeywordNameDialog(kw_ctrl, item=kw_ctrl.data)
        wx.CallAfter(dlg.EndModal, wx.ID_OK)
        assert dlg.execute() == None

    def test_get_title(self):
        kw_ctrl = file_controller().create_keyword('Keyword it is', '${a1} | ${a2}')
        dlg = UserKeywordNameDialog(kw_ctrl, item=kw_ctrl.data)
        assert dlg.GetTitle() == 'New User Keyword'

    def test_validators(self):
        kw_ctrl = file_controller().create_keyword('Keyword it is', '${a1} | ${a2}')
        dlg = UserKeywordNameDialog(kw_ctrl, item=kw_ctrl.data)
        assert len(get_dlg_validators(dlg)) == 2

    def test_kw_validator(self):
        kw_ctrl = file_controller().create_keyword('Keyword it is', '${a1} | ${a2}')
        dlg = UserKeywordNameDialog(kw_ctrl, item=kw_ctrl.data)
        validator: UserKeywordNameValidator = get_dlg_validators(dlg)[0]
        assert isinstance(validator, UserKeywordNameValidator)

    def test_args_validator(self):
        kw_ctrl = file_controller().create_keyword('Keyword it is', '${a1} | ${a2}')
        dlg = UserKeywordNameDialog(kw_ctrl, item=kw_ctrl.data)
        validator = get_dlg_validators(dlg)[1]
        assert isinstance(validator, ArgumentsValidator)


if __name__ == '__main__':
    unittest.main()
