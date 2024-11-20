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
from robotide.namespace.namespace import _Keywords


class ItemMock(object):

    def __init__(self, name, args, long):
        self.name = name
        self.arguments = args
        self.longname = long


class TestKeywords(unittest.TestCase):

    def setUp(self):
        self.kws = _Keywords(
            [ItemMock('My kw', ['${arg}'], 'source.My kw'),
             ItemMock('Given foo', [], 'source.Given foo'),
             ItemMock('${user} should ${foo} and ${bar}', [], 'longem'),
             ItemMock('this ${has} real args', ['${arg}'], 'long.normal')])

    def test_parse_keywords(self):
        assert self.kws.get('My kw')

    def test_normalize(self):
        assert self.kws.get('mykw')
        assert self.kws.get('M Y     KW')
        assert not self.kws.get('my kw?')

    def test_underscore_normalization(self):
        assert self.kws.get('m_ykw')
        assert self.kws.get('_mY_kw_')

    def test_longname(self):
        assert self.kws.get('source.my kw')

    def test_given_when_then(self):
        assert self.kws.get('Given foo')
        assert self.kws.get('Given my kw')
        assert self.kws.get('When my kw')
        assert self.kws.get('then mykw')
        assert self.kws.get('and  given foo')
        assert self.kws.get('But my kw')

    def test_embedded_args(self):
        assert self.kws.get('john should embed arguments and something')
        assert self.kws.get('WHEN john should embed arguments and something')
        assert self.kws.get('but john should embed arguments and something')
        assert self.kws.get('this keyword has real args')  # Now it is possible to have normal arguments

    def test_embedded_args_are_space_sensitive(self):
        assert not self.kws.get('john shouldembed arguments and something')
        assert not self.kws.get('given johnshould embed arguments and something')

    def test_first_come_prioritized_when_same_short_name(self):
        kws = _Keywords([ItemMock('My kw', ['${arg}'], 'source.My kw'),
                         ItemMock('My kw', [], 'Collision!')])
        assert kws.get('My kw').arguments == ['${arg}']
        assert kws.get('Collision!').arguments == []


if __name__ == "__main__":
    unittest.main()
