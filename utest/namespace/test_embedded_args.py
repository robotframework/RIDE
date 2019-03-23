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
from robotide.namespace.embeddedargs import EmbeddedArgsHandler
from nose.tools import assert_true, assert_raises, assert_false


class KWMock(object):

    def __init__(self, name, args=None):
        self.name = name
        self.arguments = args


class TestEmbeddedArgs(unittest.TestCase):

    def test_extra_arguments_are_illegal(self):
        assert_raises(TypeError, EmbeddedArgsHandler,
                            KWMock('add user ${user} to db', ['${arg}']))

    def test_no_embedded_arguments(self):
        assert_raises(TypeError, EmbeddedArgsHandler,
                            KWMock('no embedded args'))

    def test_embedded_args(self):
        args = EmbeddedArgsHandler(KWMock('add user ${user} to db'))
        assert_true(args.name_regexp.match('add user test to db'))
        assert_false(args.name_regexp.match('add user test to somewhere else'))

    def test_several_args(self):
        args = EmbeddedArgsHandler(KWMock('${user} should ${foo} and ${bar}'))
        assert_true(args.name_regexp.match('john should eat and drink'))
        assert_false(args.name_regexp.match('this should not match'))

    def test_custom_variable_regexp(self):
        args = EmbeddedArgsHandler(KWMock('Say hello to ${user:[A-C]+}'))
        assert_true(args.name_regexp.match('Say hello to ABC'))
        assert_false(args.name_regexp.match('Say hello to ABCD'))


if __name__ == "__main__":
    unittest.main()
