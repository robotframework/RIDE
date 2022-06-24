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
from robotide.ui.actiontriggers import _NameBuilder


class TestGetNameWithAccelerator(unittest.TestCase):

    def setUp(self):
        self._nb = _NameBuilder()

    def _test(self, input, expected):
        assert self._nb.get_name(input) == expected

    def test_use_first_free_char(self):
        self._test('File', '&File')
        self._test('Foo', 'F&oo')
        self._test('Foobar', 'Foo&bar')

    def test_case_insensitive(self):
        self._test('File', '&File')
        self._test('foo', 'f&oo')
        self._test('bar', '&bar')
        self._test('Barbi', 'B&arbi')

    def test_all_letters_taken(self):
        self._test('File', '&File')
        self._test('Open', '&Open')
        self._test('Foo', 'Foo')

    def test_space_is_not_used(self):
        self._test('File', '&File')
        self._test('Open', '&Open')
        self._test('Foo Bar', 'Foo &Bar')

    def test_free_given(self):
        self._test('&File', '&File')
        self._test('O&pen', 'O&pen')

    def test_non_free_given(self):
        self._test('&File', '&File')
        self._test('&Foo', 'F&oo')
        self._test('&Open', 'O&pen')
        self._test('F&oo Bar', 'Foo &Bar')
        self._test('&Fofo', 'Fofo')

    def test_get_same_acc_for_same_name(self):
        for name in 'F&ile', 'File', '&File', 'FI&LE', 'fil&e', 'file':
            self._test(name, 'F&ile')

    def test_ambersand_at_end_is_ignored(self):
        self._test('File&', '&File')

    def test_get_registered_name(self):
        self._test('&File', '&File')
        for name in 'F&ile', 'File', '&File', 'FI&LE', 'fil&e', 'file':
            assert self._nb.get_registered_name(name) == '&File'
        assert self._nb.get_registered_name('Non Existing') == None


if __name__ == '__main__':
    unittest.main()
