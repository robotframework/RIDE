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

from robotide.validators import ArgumentsValidator


class Test(unittest.TestCase):
    validate = ArgumentsValidator()._validate
    validation_error = 'List and scalar arguments must be before named and dictionary arguments'
    kwargs_validation_error = 'Only last argument can be kwargs (dictionary argument).'

    def test_valid_arguments_validation(self):
        for arg in [
            "${arg}",
            "${arg}|${arg2}",
            "${arg}=",
            "${arg}=def val",
            "${a} | ${b}=d | ${c}=\\| | ${d}=",
            "@{list}",
            "${a} | ${b} | @{f}",
            "&{dict}",
            "${arg} | &{dict}",
            "@{list} | &{dict}",
            "${a} | ${b} | @{f} | &{dict}",
            "${arg}=foo | @{list}",
            "@{varargs} | ${named}",
            "@{} | ${first} | ${second}",
            "${positional} | @{} | ${named}",
            "@{varargs} | ${named only} | ${teste} | &{free named}",
            "@{} | ${named}=default",
            "@{} | ${optional}=default | ${mandatory} | ${mandatory 2} | ${optional 2}=default 2 | ${mandatory 3}"
        ]:
            assert self.validate(arg) is None, arg

    def test_invalid_arguments_validation(self):
        for arg in ['arg', '@{list}=', '@{list}=fooness']:
            assert (self.validate(arg) == "Invalid argument syntax '%s'" % arg)
        for arg, err in [("|${a}", ""), ("${a} | ${a2} | invalid", "invalid")]:
            assert (self.validate(arg) == "Invalid argument syntax '%s'" % err)

    def test_list_arg_in_incorrect_position(self):
        for arg in ["&{dict} | @{list}"]:
            assert self.validate(arg) == self.kwargs_validation_error, arg

    def test_kwarg_in_incorrect_position(self):
        for arg in ["${positional} | @{} | &{options} | ${foo}"]:
            assert self.validate(arg) == self.validation_error, arg

    def test_req_arg_after_defaults(self):
        for arg in ["${a}=default | ${a2}", "${a} | ${b}=default | ${c}"]:
            assert self.validate(arg) == self.validation_error


if __name__ == '__main__':
    unittest.main()
