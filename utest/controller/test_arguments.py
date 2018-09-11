import unittest
from robotide.controller.arguments import parse_argument,\
    parse_arguments_to_var_dict
from nose.tools import assert_equal, assert_is_none


class TestParseArguments(unittest.TestCase):

    def test_parse(self):
        args = ['${my arg}', '${default}=huhuu', '@{list}', 'invalid${}{}{{']
        parsed = parse_arguments_to_var_dict(args, 'Keyword name')
        assert_equal(parsed['${my arg}'], '')
        assert_equal(parsed['${default}'], 'huhuu')
        assert_equal(parsed['@{list}'], [])
        assert_equal(len(parsed.keys()), 3)

    def test_parse_with_no_args(self):
        parsed = parse_arguments_to_var_dict([], 'Keyword name')
        assert_equal(len(parsed.keys()), 0)

    def test_embedded_arguments(self):
        parsed = parse_arguments_to_var_dict([], "Here is ${arg} and ${another arg}")
        assert_equal(parsed['${arg}'], None)
        assert_equal(parsed['${another arg}'], None)
        assert_equal(len(parsed.keys()), 2)

    def test_embedded_arguments_with_list_var_syntax(self):
        parsed = parse_arguments_to_var_dict([], "Here is ${arg} and @{list arg}")
        assert_equal(parsed['${arg}'], None)
        assert_equal(len(parsed.keys()), 1)

    def test_embedded_arguments_with_args(self):
        parsed = parse_arguments_to_var_dict(['${my arg}'], "Here is ${arg} and ${another arg}")
        assert_equal(parsed['${my arg}'], '')
        assert_equal(len(parsed.keys()), 1)


class TestArgument(unittest.TestCase):

    def test_simple_argument(self):
        arg = parse_argument('${my arg}')
        assert_equal(arg, ('${my arg}', ''))

    def test_list_argument(self):
        arg = parse_argument('@{my arg}')
        assert_equal(arg, ('@{my arg}', []))

    def test_default_value(self):
        arg = parse_argument('${my arg}    = huhuu')
        assert_equal(arg, ('${my arg}', 'huhuu'))

    def test_default_value_with_no_space(self):
        arg = parse_argument('${my arg}=huhuu')
        assert_equal(arg, ('${my arg}', 'huhuu'))

    def test_default_value_with_escaped_sequence(self):
        arg = parse_argument('${my arg}=huh\\}uu')
        assert_equal(arg, ('${my arg}', 'huh\\}uu'))

    def test_invalid_argument(self):
        name, value = parse_argument('${my invalid')
        assert_is_none(name)
        assert_is_none(value)


if __name__ == "__main__":
    unittest.main()
