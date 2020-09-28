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
from utest.resources import datafilereader
from robotide.controller.ctrlcommands import ExtractScalar, ExtractList
from nose.tools import assert_equal


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
        assert_equal(self.testcase.step(row).as_list()[col], var_name)
        var = [var for var in self.testcase.datafile_controller.variables if var.name == var_name][0]
        assert_equal(var.value[0], var_value)
        assert_equal(var.comment.as_list(), var_comment)

    def test_list_extract(self):
        row = 0
        cols = [2, 3]
        var_name = '@{joo}'
        var_value = self.testcase.step(row).as_list()[cols[0]:cols[-1]+1]
        value_after_list = self.testcase.step(row).as_list()[cols[-1]+1]
        var_comment = ['Comment for my test list']
        self.testcase.execute(ExtractList(var_name, var_value, var_comment, [(row, col) for col in cols]))
        assert_equal(self.testcase.step(row).as_list()[cols[0]], var_name)
        var = [var for var in self.testcase.datafile_controller.variables if var.name == var_name][0]
        assert_equal(var.value, var_value)
        assert_equal(var.comment.as_list(), var_comment)
        assert_equal(self.testcase.step(row).as_list()[cols[0]+1], value_after_list)


if __name__ == "__main__":
    unittest.main()
