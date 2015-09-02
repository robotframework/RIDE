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
