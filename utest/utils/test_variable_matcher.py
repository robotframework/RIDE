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
from robotide.utils.variablematcher import *


class _BaseTestIsVariable(object):
    var_name = None
    var_with_curly_bracket = None

    def test_variable_only(self):
        assert self._test_method(self.var_name)
        assert self._test_method(self.var_with_curly_bracket)

    def test_variable_with_equal_sign(self):
        assert self._test_method('%s = ' % self.var_name)
        assert self._test_method('%s= ' % self.var_name)
        assert self._test_method('%s=' % self.var_name)

    def test_variable_part_of_string_should_not_match(self):
        assert not self._test_method('some %s variable' % self.var_name)
        assert not self._test_method('some %s' % self.var_name)
        assert not self._test_method('%s variable' % self.var_name)
        assert not self._test_method('%s123' % self.var_name)
        assert not self._test_method('%s some text %s' % (self.var_name, self.var_name))


class TestIsScalarVariable(_BaseTestIsVariable, unittest.TestCase):
    var_name = "${var name}"
    var_with_curly_bracket = r"${var \}}"

    @staticmethod
    def _test_method(value):
        return is_scalar_variable(value)


class TestIsListVariable(_BaseTestIsVariable, unittest.TestCase):
    var_name = "@{var name}"
    var_with_curly_bracket = r"@{var \}}"

    @staticmethod
    def _test_method(value):
        return is_list_variable(value)

    def test_variable_with_index(self):
        assert is_list_variable('@{list}[21]')

    def test_list_variable_subitem(self):
        assert is_list_variable_subitem('@{SOME_LIST}[3]')
        assert not is_list_variable_subitem('@{justlist}')


class TestGetVariable(unittest.TestCase):

    def test_get_scalar_variable(self):
        assert get_variable('${var}') == '${var}'
        assert get_variable('${var} = ') == '${var}'

    def test_get_list_variable(self):
        assert get_variable('@{var}') == '@{var}'
        assert get_variable('@{var} = ') == '@{var}'
        assert get_variable('@{var}[2]') == '@{var}'

    def test_variable_not_found(self):
        assert get_variable('{not var}') is None


class TestGetVariableBaseName(unittest.TestCase):

    def test_list_variable(self):
        assert get_variable_basename('@{list var}') == '@{list var}'
        assert get_variable_basename('@{list var} =') == '@{list var}'

    def test_attribute_accessed_with_extended_var_syntax(self):
        assert get_variable_basename('${var name.some_attr}') == '${var name}'

    def test_method_accessed_with_extended_var_syntax(self):
        assert get_variable_basename('${var name.method()}') == '${var name}'

    def test_slice_accessed_with_extended_var_syntax(self):
        assert get_variable_basename('${var name[6]}') == '${var name}'

    def test_calculation_accessed_with_extended_var_syntax(self):
        assert get_variable_basename('${var name + 1 -${23}}') == '${var name}'


class TestFindVariables(unittest.TestCase):

    def test_find_variables_without_var(self):
        assert find_variable_basenames('some data') == []

    def test_find_variables(self):
        assert (find_variable_basenames('some ${var} and ${another var}') == ['${var}', '${another var}'])

    def test_find_scalar_and_list_variable(self):
        assert (find_variable_basenames('some ${var} and @{another var}') == ['${var}', '@{another var}'])

    def test_find_scalar_with_extended_var_syntax(self):
        assert (find_variable_basenames('some ${var.attr} and ${another var.method()}') == ['${var}', '${another var}'])

    def test_finding_multiple_variables(self):
        assert (find_variable_basenames('hu ${huhu + 5} pupu ${foo} uhhu ${gugy.gug sdknjs +enedb} {{]{}{}{[[}') ==
                ['${huhu}', '${foo}', '${gugy}'])

    def test_finding_variables_when_variable_inside_variable(self):
        assert (find_variable_basenames('some ${var + ${another}} inside') ==
                ['${var}'])  # We do not support variables inside vars at the moment


if __name__ == "__main__":
    unittest.main()
