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
import robotide


class ArgumentParsingTestCase(unittest.TestCase):

    def test_no_args(self):
        self._assert_args([])

    def _assert_args(self, tested, expected_no_update_check=False, expected_debug_console=False, expected_path=None):
        self.assertEqual((expected_no_update_check, expected_debug_console, expected_path), robotide._parse_args(tested))

    def test_path_to_data(self):
        self._assert_args(['data'], expected_path='data')

    def test_noupdatecheck(self):
        self._assert_args(['--noupdatecheck'], expected_no_update_check=True)

    def test_noupdatecheck_and_path(self):
        self._assert_args(['--noupdatecheck', 'path'], expected_no_update_check=True, expected_path='path')

    def test_debugconsole(self):
        self._assert_args(['--debugconsole'], expected_debug_console=True)

    def test_debugconsole_and_path(self):
        self._assert_args(['--debugconsole', 'dir'], expected_debug_console=True, expected_path='dir')

if __name__ == '__main__':
    unittest.main()
