#  Copyright 2023-     Robot Framework Foundation
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

import copy
import sys
import unittest
import pytest


class TestMain(unittest.TestCase):

    def test_missing_wx(self):  # This test passes when running alone, but fails when all
        old_path = copy.deepcopy(sys.path)
        indexes = [idx for idx, s in enumerate(sys.path) if 'python' in s.lower()]
        for idx in indexes:
            sys.path[idx] = ''
        try:
            with pytest.raises((ImportError, ModuleNotFoundError, SystemExit)):
                import robotide
                print(dir(robotide))
        finally:
            sys.path = old_path

    def test_main_call_with_extra_args(self):
        from robotide import main
        with pytest.raises(SystemExit):
            main('--noupdatecheck', '--debugconsole', '--version', 'test.robot')

    def test_main_call_with_help(self):
        from robotide import main
        with pytest.raises(SystemExit):
            result = main('--noupdatecheck', '--debugconsole', '--help')
            assert result.startswith('RIDE')

    def test_main_call_with_version(self):
        from robotide import main
        with pytest.raises(SystemExit):
            result = main('--version')
            print(f"DEBUG: Result is {result}")
            assert result.startswith('v2.0')


if __name__ == '__main__':
    unittest.main()
