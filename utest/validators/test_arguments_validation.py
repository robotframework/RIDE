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

from nose.tools import assert_equal


class Test(unittest.TestCase):
    validate = ArgumentsValidator()._validate
    validation_error = \
        'List and scalar arguments must be before named and dictionary arguments'

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
                "${arg}=foo | @{list}"
        ]:
            assert_equal(self.validate(arg), None, arg)

    def test_invalid_arguments_validation(self):
        for arg in ['arg', '@{list}=', '@{list}=fooness']:
            assert_equal(self.validate(arg),
                          "Invalid argument syntax '%s'" % arg)
        for arg, err in [("|${a}", ""), ("${a} | ${a2} | invalid", "invalid")]:
            assert_equal(self.validate(arg),
                          "Invalid argument syntax '%s'" % err)

    def test_list_arg_in_incorrect_position(self):
        for arg in ["@{list} | ${foo}",
                    "&{dict} | @{list}"]:
            assert_equal(self.validate(arg), self.validation_error, arg)

    def test_req_arg_after_defaults(self):
        for arg in ["${a}=default | ${a2}",
                    "${a} | ${b}=default | ${c}"]:
            assert_equal(self.validate(arg), self.validation_error)
