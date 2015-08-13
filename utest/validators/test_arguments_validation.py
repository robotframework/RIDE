import unittest

from robotide.validators import ArgumentsValidator

from robot.utils.asserts import assert_equals, assert_none


class Test(unittest.TestCase):
    validate = ArgumentsValidator()._validate
    validation_error = \
        'List and scalar arguments must be beforenamed and dictionary arguments'

    def test_valid_arguments_validation(self):
        for arg in [
                "${arg}",
                "${arg}|${arg2}",
                "${arg}=",
                "${arg}=def val",
                "${a} | ${b}=d | ${c}=\\| | ${d}=",
                "@{list}",
                "@{list} | ${arg}",
                "${a} | ${b} | @{f}",
                "&{dict}",
                "${arg} | &{dict}",
                "@{list} | &{dict}",
                "${a} | ${b} | @{f} | &{dict}",
        ]:
            assert_none(self.validate(arg), arg)

    def test_invalid_arguments_validation(self):
        for arg in ["arg", "@{list}=", "@{list}=fooness"]:
            assert_equals(self.validate(arg),
                          "Invalid argument syntax '%s'" % arg)
        for arg, err in [("|${a}", ""), ("${a} | ${a2} | invalid", "invalid")]:
            assert_equals(self.validate(arg),
                          "Invalid argument syntax '%s'" % err)

    def test_list_arg_in_incorrect_poition(self):
        for arg in ["${arg}=foo | @{list}",
                    "&{dict} | @{list}"]:
            assert_equals(self.validate(arg), self.validation_error)

    def test_req_arg_after_defaults(self):
        for arg in ["${a}=default | ${a2}",
                    "${a} | ${b}=default | ${c}"]:
            assert_equals(self.validate(arg), self.validation_error)
