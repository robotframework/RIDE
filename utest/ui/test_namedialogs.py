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
from nose.tools import assert_equal
from robotide.controller.filecontrollers import TestCaseFileController
from robotide.editor.editordialogs import (
    TestCaseNameDialog, UserKeywordNameDialog)
from robotide.robotapi import TestCaseFile
# from resources import PYAPP_REFERENCE, wx


def file_controller():
    return TestCaseFileController(TestCaseFile())


class TestNameDialogTest(unittest.TestCase):
    # _frame = wx.Frame(None)

    def test_creation(self):
        test_ctrl = file_controller().create_test('A test')
        dlg = TestCaseNameDialog(test_ctrl)
        assert_equal(dlg.get_name(), '')


class TestUserKeywordNameDialog(unittest.TestCase):

    def test_creation(self):
        kw_ctrl = file_controller().create_keyword('Keyword it is')
        dlg = UserKeywordNameDialog(kw_ctrl)
        assert_equal(dlg.get_name(), '')

    def test_arguments_are_returned(self):
        kw_ctrl = file_controller().create_keyword('Keyword it is')
        dlg = UserKeywordNameDialog(kw_ctrl)
        assert_equal(dlg.get_args(), '')


if __name__ == '__main__':
    unittest.main()
