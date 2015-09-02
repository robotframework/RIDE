import unittest
from nose.tools import assert_equals

from robotide.controller.filecontrollers import TestCaseFileController
from robotide.editor.editordialogs import (
    TestCaseNameDialog, UserKeywordNameDialog)
from robotide.robotapi import TestCaseFile

from resources import PYAPP_REFERENCE, wx


def file_controller():
    return TestCaseFileController(TestCaseFile())


class TestNameDialogTest(unittest.TestCase):
    _frame = wx.Frame(None)

    def test_creation(self):
        test_ctrl = file_controller().create_test('A test')
        dlg = TestCaseNameDialog(test_ctrl)
        assert_equals(dlg.get_name(), '')


class UserKeywordNameDialogTest(unittest.TestCase):

    def test_creation(self):
        kw_ctrl = file_controller().create_keyword('Keyword it is')
        dlg = UserKeywordNameDialog(kw_ctrl)
        assert_equals(dlg.get_name(), '')

    def test_arguments_are_returned(self):
        kw_ctrl = file_controller().create_keyword('Keyword it is')
        dlg = UserKeywordNameDialog(kw_ctrl)
        assert_equals(dlg.get_args(), '')
