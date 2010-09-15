import unittest
from robot.parsing.model import TestCaseFile
from robot.utils.asserts import assert_equals

from robotide.controller.filecontroller import TestCaseFileController
from robotide.editor.editordialogs import TestCaseNameDialog, UserKeywordNameDialog

from resources import PYAPP_REFERENCE


def file_controller():
    return TestCaseFileController(TestCaseFile())


class TestNameDialogTest(unittest.TestCase):

    def test_creation(self):
        test_ctrl = file_controller().new_test('A test')
        dlg = TestCaseNameDialog(None, test_ctrl)
        assert_equals(dlg.get_name(), '')


class UserKeywordNameDialogTest(unittest.TestCase):

    def test_creation(self):
        kw_ctrl = file_controller().new_keyword('Keyword it is')
        dlg = UserKeywordNameDialog(None, kw_ctrl)
        assert_equals(dlg.get_name(), '')

    def test_arguments_are_returned(self):
        kw_ctrl = file_controller().new_keyword('Keyword it is')
        dlg = UserKeywordNameDialog(None, kw_ctrl)
        assert_equals(dlg.get_args(), '')
