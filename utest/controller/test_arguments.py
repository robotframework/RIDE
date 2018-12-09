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
