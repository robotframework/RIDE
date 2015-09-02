import unittest
import datafilereader
from robotide.controller.commands import ExtractScalar, ExtractList
from nose.tools import assert_equals


class TestExtractVariableCommands(unittest.TestCase):

    def setUp(self):
        self.project_ctrl = datafilereader.construct_project(datafilereader.LOG_MANY_SUITE)
        self.datafile = datafilereader.get_ctrl_by_name('Log Many', self.project_ctrl.datafiles)
        self.testcase = self.datafile.tests[0]

    def tearDown(self):
        self.project_ctrl.close()

    def test_scalar_extract(self):
        row, col = 0, 1
        var_name = '${foo}'
        var_value = self.testcase.step(row).as_list()[col]
        var_comment = ['Something about the variable']
        self.testcase.execute(ExtractScalar(var_name, var_value, var_comment, (row, col)))
        assert_equals(self.testcase.step(row).as_list()[col], var_name)
        var = [var for var in self.testcase.datafile_controller.variables if var.name == var_name][0]
        assert_equals(var.value[0], var_value)
        assert_equals(var.comment.as_list(), var_comment)

    def test_list_extract(self):
        row = 0
        cols = [2, 3]
        var_name = '@{joo}'
        var_value = self.testcase.step(row).as_list()[cols[0]:cols[-1]+1]
        value_after_list = self.testcase.step(row).as_list()[cols[-1]+1]
        var_comment = ['Comment for my test list']
        self.testcase.execute(ExtractList(var_name, var_value, var_comment, [(row, col) for col in cols]))
        assert_equals(self.testcase.step(row).as_list()[cols[0]], var_name)
        var = [var for var in self.testcase.datafile_controller.variables if var.name == var_name][0]
        assert_equals(var.value, var_value)
        assert_equals(var.comment.as_list(), var_comment)
        assert_equals(self.testcase.step(row).as_list()[cols[0]+1], value_after_list)


if __name__ == "__main__":
    unittest.main()
