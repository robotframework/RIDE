import unittest
from robot.utils.asserts import assert_equals, assert_none

from robotide.model.tables import VariableTable
from resources import FakeSuite


class TestVariables(unittest.TestCase):

    def setUp(self):
       self.vars = VariableTable(FakeSuite())
       self.vars.new_scalar_var('${foo}', 'value')
       self.vars.new_list_var('@{list}', ['value','another'])

    def test_validating_varible_names(self):
        assert_equals(self.vars.validate_scalar_variable_name('${foo}'),
                      'Variable with this name already exists.')
        assert_equals(self.vars.validate_list_variable_name('@{list}'),
                      'Variable with this name already exists.')

    def test_validation_is_case_insensitive(self):
        assert_equals(self.vars.validate_scalar_variable_name('${FoO}'),
                      'Variable with this name already exists.')
        assert_equals(self.vars.validate_list_variable_name('@{liSt}'),
                      'Variable with this name already exists.')

    def test_invalid_name(self):
        assert_equals(self.vars.validate_scalar_variable_name('invalid'),
                      'Scalar variable name must be in format ${name}')
        assert_equals(self.vars.validate_list_variable_name('invalid'),
                      'List variable name must be in format @{name}')




