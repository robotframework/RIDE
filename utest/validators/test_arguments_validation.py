#  Copyright 2008 Nokia Siemens Networks Oyj
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

from robot.utils.asserts import assert_equals, assert_none

from robotide.validators import ArgumentsValidator


class Test(unittest.TestCase):
    validate = ArgumentsValidator()._validate

    def test_valid_arguments_validation(self):
        for arg in ["${arg}", "${arg}|${arg2}", "${arg}=", "${arg}=default val", 
                    "${a} | ${b}=d | ${c}=\\| | ${d}=", "@{list}",
                    "${a} | ${b} | ${c}=1 | ${d}=2 | ${e}=3 | @{f}"]:
            assert_none(self.validate(arg))

    def test_invalid_arguments_validation(self):
        for arg in ["arg", "@{list}=", "@{list}=fooness"]:
            assert_equals(self.validate(arg),
                          "Invalid argument syntax '%s'" % arg)
        for arg, err in [("|${a}", ""), ("${a} | ${a2} | invalid", "invalid")]:
            assert_equals(self.validate(arg),
                          "Invalid argument syntax '%s'" % err)

    def test_list_arg_not_last(self):
        for arg in ["@{list} | ${arg}", "@{list} | ${arg} | @{list2}", 
                    "@{list} | ${arg}=foo", "@{list} | @{list2}"]:
            assert_equals(self.validate(arg),
                          "List variable allowed only as the last argument")

    def test_req_arg_after_defaults(self):
        for arg in ["${a}=default | ${a2}", "${a} | ${b}=default | ${c}"]:
            assert_equals(self.validate(arg),
                          "Required arguments not allowed after arguments "
                          "with default values.")


if __name__ == "__main__":
    unittest.main()
