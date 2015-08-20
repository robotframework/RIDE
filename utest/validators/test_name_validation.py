import unittest

from robotide.robotapi import VariableTable, KeywordTable, TestCaseTable
from robotide.controller.macrocontrollers import (
    UserKeywordController, TestCaseController)
from robotide.controller.tablecontrollers import (
    VariableTableController, KeywordTableController, TestCaseTableController)
from robotide.validators import (
    ScalarVariableNameValidator, ListVariableNameValidator,
    UserKeywordNameValidator, TestCaseNameValidator)


class _NameValidationTest(object):

    def mock_ctrl(self):
        self.datafile = self
        self.datafile_controller = self
        self.mark_dirty = lambda: 0
        self.update_namespace = lambda: 0
        self.register_for_namespace_updates = lambda *args: 0

    def test_new_name_validation_pass(self):
        self.assertTrue(self.validate('NewName'))

    def test_new_name_validation_fails_when_same_already_exists(self):
        self.add_named('Exists')
        self.assertFalse(self.validate('Exists'))

    def test_new_name_validation_fails_when_normalized_same_already_exists(self):
        self.add_named('NoRmAliZeD')
        self.assertFalse(self.validate('Normalized'))

    def test_rename_validation_pass(self):
        self.assertTrue(self.rename_validate('Old', 'New'))

    def test_rename_validation_fails_when_same_already_exists(self):
        self.add_named('ThisIsAlreadyInThere')
        self.assertFalse(self.rename_validate('Old', 'ThisIsAlreadyInThere'))

    def test_rename_validation_pass_when_different_than_previous_but_normalized_eq(self):
        self.assertTrue(self.rename_validate('NorMALIzed', 'N_O_R_M_A_L_I_zed'))


class _VariableNameValidationTest(_NameValidationTest):

    def setUp(self):
        self._variable_table_ctrl = VariableTableController(
            self, VariableTable(self))
        self.mock_ctrl()

    def add_named(self, name):
        self._variable_table_ctrl.add_variable(
            '%s{%s}' % (self.symbol, name), 'value')

    def validate(self, name, old=None):
        self._validator = self.validator_class(self._variable_table_ctrl, old)
        return self._validator._validate('%s{%s}' % (self.symbol, name)) == ''

    def rename_validate(self, old, new):
        self.add_named(old)
        return self.validate(new, '%s{%s}' % (self.symbol, old))


class ScalarNameValidationTest(_VariableNameValidationTest, unittest.TestCase):
    symbol = '$'
    validator_class = ScalarVariableNameValidator


class ListVariableNameValidationTest(_VariableNameValidationTest, unittest.TestCase):
    symbol = '@'
    validator_class = ListVariableNameValidator


class _MacroNameValidationTest(_NameValidationTest):

    def setUp(self):
        self.mock_ctrl()
        self._table_ctrl = self.table_ctrl_class(self, self.table_class(self))
        self._ctrl = self.ctrl_class(self._table_ctrl, self)

    def add_named(self, name):
        return self._ctrl._parent.new(name)

    def validate(self, name, old=None):
        validator = self.validator_class(self._ctrl, old)
        return validator._validate(name) == ''

    def rename_validate(self, old, new):
        self._ctrl = self.add_named(old)
        return self.validate(new, old)


class KeywordNameValidationTest(_MacroNameValidationTest, unittest.TestCase):
    table_class = KeywordTable
    table_ctrl_class = KeywordTableController
    ctrl_class = UserKeywordController
    validator_class = UserKeywordNameValidator


class TestCaseNameValidationTest(_MacroNameValidationTest, unittest.TestCase):
    table_class = TestCaseTable
    table_ctrl_class = TestCaseTableController
    ctrl_class = TestCaseController
    validator_class = TestCaseNameValidator
