import unittest
from robotide.controller.arguments import parse_argument,\
    parse_arguments_to_var_dict
from robot.utils.asserts import assert_equals, assert_none


class TestParseArguments(unittest.TestCase):

    def test_parse(self):
        args = ['${my arg}', '${default}=huhuu', '@{list}', 'invalid${}{}{{']
        parsed = parse_arguments_to_var_dict(args)
        assert_equals(parsed['${my arg}'], None)
        assert_equals(parsed['${default}'], 'huhuu')
        assert_equals(parsed['@{list}'], None)
        assert_equals(len(parsed.keys()), 3)


class TestArgument(unittest.TestCase):

    def test_simple_argument(self):
        arg = parse_argument('${my arg}')
        assert_equals(arg, ('${my arg}', None))

    def test_list_argument(self):
        arg = parse_argument('@{my arg}')
        assert_equals(arg, ('@{my arg}', None))

    def test_default_value(self):
        arg = parse_argument('${my arg}    = huhuu')
        assert_equals(arg, ('${my arg}', 'huhuu'))

    def test_default_value_with_no_space(self):
        arg = parse_argument('${my arg}=huhuu')
        assert_equals(arg, ('${my arg}', 'huhuu'))

    def test_default_value_with_escaped_sequence(self):
        arg = parse_argument('${my arg}=huh\\}uu')
        assert_equals(arg, ('${my arg}', 'huh\\}uu'))

    def test_invalid_argument(self):
        arg = parse_argument('${my invalid')
        assert_none(arg)


if __name__ == "__main__":
    unittest.main()