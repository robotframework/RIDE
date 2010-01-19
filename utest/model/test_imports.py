#  Copyright 2008 Nokia Siemens Networks Oyj
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
from robot.utils.asserts import assert_equals

from robotide.model.tables import ImportSettings


class _ParsedImport(object):
    """Imitates import setting in test data parsed by RF."""
    def __init__(self, name, item):
        self.name = name
        self._item = item

class _ImportItem(object):
    def __init__(self, value):
        self.value = value


class TestAutomaticHandlingOfFileSeparatorVariable(unittest.TestCase):
    """'${/}' should be converted to '/' in import setting names, since RF
    supports the latter both in Windows and Linux.
    """
    def setUp(self):
        self._imports = ImportSettings(datafile=None, data=
                [_ParsedImport('Library', _ImportItem(['${/}some${/}path'])),
                 _ParsedImport('Resource', _ImportItem(['..${/}resources'])),
                 _ParsedImport('Variables', _ImportItem(['vars${/}first.py',
                                                         'arg${/}value']))
                 ])

    def test_(self):
        assert_equals(self._imports[0].name, '/some/path')
        assert_equals(self._imports[1].name, '../resources')
        assert_equals(self._imports[2].name, 'vars/first.py')

    def test_variable_is_not_replaced_in_arguments(self):
        assert_equals(self._imports[2].args, ['arg${/}value'])


if __name__ == '__main__':
    unittest.main()
