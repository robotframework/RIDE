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

import unittest
import pytest
from pytest import MonkeyPatch
import builtins

real_import = builtins.__import__


def myimport(name, globals, locals, fromlist, level):
    # DEBUG print(f"DEBUG: called myimport! name={name}")
    if name == 'wx':
        return real_import('wx_error', globals, locals, fromlist, level)
    if name == '':  # This is when is called "from . import version"
        raise ImportError
    return real_import(name, globals, locals, fromlist, level)


class TestWxImport(unittest.TestCase):

    def tearDown(self):
        builtins.__import__ = real_import

    def test_missing_wx(self):  # This test passed in PyCharm but not when run in command line
        builtins.__import__ = myimport
        with pytest.raises((ModuleNotFoundError, SystemExit)):  # (ImportError, ModuleNotFoundError, SystemExit)):
            import robotide
            print(dir(robotide))


class TestMain(unittest.TestCase):

    def tearDown(self):
        builtins.__import__ = real_import

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

    def test_main_call_with_fail_version(self):
        import robotide
        with MonkeyPatch().context():
            with pytest.raises((ImportError, SystemExit)):
                builtins.__import__ = myimport
                result = robotide.main('--version')  # Need to capture output
                # DEBUG print(f"DEBUG: Result is {result}")
                assert result.startswith('v2.0')

    def test_parse_args(self):
        from robotide import _parse_args
        noupdatecheck, debug_console, inpath = _parse_args(args=None)
        assert (noupdatecheck, debug_console, inpath) == (False, False, None)
        noupdatecheck, debug_console, inpath = _parse_args(args=('--noupdatecheck', 'no file'))
        assert (noupdatecheck, debug_console, inpath) == (True, False, 'no file')
        noupdatecheck, debug_console, inpath = _parse_args(args=('--noupdatecheck', '--debugconsole'))
        assert (noupdatecheck, debug_console, inpath) == (True, True, None)
        noupdatecheck, debug_console, inpath = _parse_args(args='')
        assert (noupdatecheck, debug_console, inpath) == (False, False, None)
        noupdatecheck, debug_console, inpath = _parse_args(args=('--garbagein', '--garbageout'))
        assert (noupdatecheck, debug_console, inpath) == (False, False, '--garbageout')  # returns always last arg


if __name__ == '__main__':
    unittest.main()
