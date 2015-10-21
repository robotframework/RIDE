import unittest

from robotide.validators import ArgumentsValidator

from nose.tools import assert_equals


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
            assert_equals(self.validate(arg), None, arg)

    def test_invalid_arguments_validation(self):
        for arg in ["arg", "@{list}=", "@{list}=fooness"]:
            assert_equals(self.validate(arg),
                          "Invalid argument syntax '%s'" % arg)
        for arg, err in [("|${a}", ""), ("${a} | ${a2} | invalid", "invalid")]:
            assert_equals(self.validate(arg),
                          "Invalid argument syntax '%s'" % err)

    def test_list_arg_in_incorrect_position(self):
        for arg in ["@{list} | ${foo}",
                    "&{dict} | @{list}"]:
            assert_equals(self.validate(arg), self.validation_error, arg)

    def test_req_arg_after_defaults(self):
        for arg in ["${a}=default | ${a2}",
                    "${a} | ${b}=default | ${c}"]:
            assert_equals(self.validate(arg), self.validation_error)
