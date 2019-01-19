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

from robotide.robotapi import Variable
from robotide.controller.settingcontrollers import VariableController


class TestVariableEquality(unittest.TestCase):

    def setUp(self):
        self._var = Variable(object(), '${steve}', 'val')
        self._var_ctrl = VariableController(object(), self._var)

    def test_is_not_equal_to_none(self):
        self.assertFalse(self._var_ctrl == None)

    def test_is_equal_to_self(self):
        self.assertTrue(self._var_ctrl == self._var_ctrl)

    def test_is_not_equal_to_some_other(self):
        self.assertFalse(self._var_ctrl == \
            VariableController(object(), Variable(object(), '${other}', 'foo')))

    def test_is_equal_if_same_underlining_var(self):
        other = VariableController(object(), self._var)
        self.assertTrue(self._var_ctrl == other)

    def test_comment_variable(self):
        self.assertTrue(self._var_ctrl.has_data())
        self.assertFalse(VariableController(object(), Variable(object(), '','')).has_data())

if __name__ == '__main__':
    unittest.main()
