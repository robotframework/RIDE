import unittest
import datafilereader
from robot.utils.asserts import assert_true, assert_false, assert_equals
from robotide.controller.commands import MoveTo


class TestMoveCommand(unittest.TestCase):

    # NOTE! The data is shared among tests and they change the data
    # This is for performance reasons but be warned when you add tests!
    @classmethod
    def setUpClass(cls):
        ctrl = datafilereader.construct_chief_controller(datafilereader.OCCURRENCES_PATH)
        cls.ts1 = datafilereader.get_ctrl_by_name('TestSuite1', ctrl.datafiles)
        cls.ts2 = datafilereader.get_ctrl_by_name('TestSuite2', ctrl.datafiles)
        cls.resu = datafilereader.get_ctrl_by_name(datafilereader.OCCURRENCES_RESOURCE_NAME, ctrl.datafiles)

    def test_move_variable_from_suite_to_another_suite(self):
        self._move_variable(self.ts1.variables[0], self.ts1, self.ts2)

    def test_move_variable_from_suite_to_resource_file(self):
        self._move_variable(self.ts1.variables[0], self.ts1, self.resu)

    def test_move_variable_from_resource_to_suite(self):
        self._move_variable(self.resu.variables[0], self.resu, self.ts2)

    def _move_variable(self, what, from_where, to_where):
        what.execute(MoveTo(to_where))
        name, value = what.name, what.value
        assert_true((name, value) in [(v.name,v.value) for v in to_where.variables])
        assert_false((name, value) in [(v.name,v.value) for v in from_where.variables])

    def test_move_testcase_from_suite_to_another_suite(self):
        test_from_suite2 = self.ts2.tests[1]
        test_from_suite2.execute(MoveTo(self.ts1))
        assert_equals(test_from_suite2, self.ts1.tests[1])
        assert_equals(len(self.ts2.tests), 1)

    def test_move_keyword_from_suite_to_another_suite(self):
        kw_from_suite1 = self.ts1.keywords[1]
        kw_from_suite1.execute(MoveTo(self.ts2))
        assert_equals(kw_from_suite1, self.ts2.keywords[1])
        assert_equals(len(self.ts1.keywords), 1)



if __name__ == "__main__":
    unittest.main()