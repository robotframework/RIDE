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
import sys
import unittest
import pytest
from pytest import MonkeyPatch
import builtins

real_import = builtins.__import__


def myimport(name, globals, locals, fromlist, level):
    # DEBUG print(f"DEBUG: called myimport! name={name}")
    if name == 'wx.lib.inspection':  # in ['wx', 'Colour', 'wx.lib.inspection']:
        raise ModuleNotFoundError  # real_import('wx_error', globals, locals, fromlist, level)
    if name == '' or name == 'robotide.application':  # This '' is when is called "from . import version"
        raise ModuleNotFoundError
    return real_import(name, globals, locals, fromlist, level)


# DEBUG: This fails when running with other tests.
class TestWxImport(unittest.TestCase):

    def tearDown(self):
        builtins.__import__ = real_import

    @pytest.mark.order(1)
    def test_missing_wx(self):  # This test passed in PyCharm but not when run in command line
        with MonkeyPatch().context() as m:
            with pytest.raises((ModuleNotFoundError, SystemExit)):  # (ImportError, ModuleNotFoundError, SystemExit)):
                sys.modules.pop('wx.lib.inspection', None)
                builtins.__import__ = myimport
                import robotide
                print(dir(robotide))


builtins.__import__ = real_import


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
                assert result.startswith('v2.0.7')

    def test_parse_args(self):
        from robotide import _parse_args
        noupdatecheck, debug_console, settings_path, inpath = _parse_args(args=None)
        assert (noupdatecheck, debug_console, settings_path, inpath) == (False, False, None, None)
        noupdatecheck, debug_console, settings_path, inpath = _parse_args(args=('--noupdatecheck', 'no file'))
        assert (noupdatecheck, debug_console, settings_path, inpath) == (True, False, None, 'no file')
        noupdatecheck, debug_console, settings_path, inpath = _parse_args(args=('--noupdatecheck', '--debugconsole'))
        assert (noupdatecheck, debug_console, settings_path, inpath) == (True, True, None, None)
        noupdatecheck, debug_console, settings_path, inpath = _parse_args(args=('--noupdatecheck', '--debugconsole',
                                                                                '--settingspath', 'mysettings.cfg',
                                                                                'my_test_suite'))
        assert (noupdatecheck, debug_console, settings_path, inpath) == (True, True, 'mysettings.cfg', 'my_test_suite')
        noupdatecheck, debug_console, settings_path, inpath = _parse_args(args='')
        assert (noupdatecheck, debug_console, settings_path, inpath) == (False, False, None, None)
        noupdatecheck, debug_console, settings_path, inpath = _parse_args(args=('--garbagein', '--garbageout'))
        # returns always first arg
        assert (noupdatecheck, debug_console, settings_path, inpath) == (False, False, None, '--garbagein')

    def test_run_call_with_fail_import(self):
        import robotide.application

        def side_effect(one: bool= False, two: bool= False):
            print(f"DEBUG: side_effect Called with {one=} {two=}")

        with MonkeyPatch().context() as m:
            m.setattr(robotide, '_show_old_wxpython_warning_if_needed', side_effect)
            with pytest.raises(ImportError):
                builtins.__import__ = myimport
                robotide._run(False, False)

    def test_run_call_with_old_version(self):
        import robotide.application
        import wx

        def my_show(*args):
            print("DEBUG:Called my_main")

        from robotide.application import RIDE

        with MonkeyPatch().context() as ctx:
            myapp = wx.App(None)

            class SideEffect(RIDE):

                def __init__(self, path=None, updatecheck=True, settingspath=None):
                    self.frame = wx.Frame(None)

                def OnInit(self):  # Overrides wx method
                    pass

                def MainLoop(self):  # Overrides wx method
                    pass

            with MonkeyPatch().context() as m:
                m.setattr(robotide.application, 'RIDE', SideEffect)
                import wx
                m.setattr(wx, 'VERSION', (4, 0, 0, '', ''))
                from wx import MessageDialog
                m.setattr(MessageDialog, 'ShowModal', my_show)
                robotide._run(False, False, False, None)

    def test_run_call_with_new_version_dbg_console(self):
        import robotide.application
        import wx

        with MonkeyPatch().context() as ctx:
            myapp = wx.App(None)

            def my_show(*args):
                print("DEBUG:Called my_show")

            def my_start(*args):
                print("DEBUG:Called my_start")

            from robotide.application import RIDE

            class SideEffect(RIDE):

                def __init__(self, path=None, updatecheck=True, settingspath=None):
                    self.frame = wx.Frame(None)

                def OnInit(self):
                    pass

                def MainLoop(self):
                    pass

            with MonkeyPatch().context() as m:
                from wx.lib.inspection import InspectionTool
                from robotide.application import debugconsole
                m.setattr(InspectionTool, 'Show', my_show)
                m.setattr(debugconsole, 'start', my_start)
                m.setattr(robotide.application, 'RIDE', SideEffect)
                import wx
                m.setattr(wx, 'VERSION', (4, 4, 0, '', ''))
                robotide._run(False, False, True, None)

    def test_main_call_with_fail_run(self):
        import robotide

        def my_run(*args):
            print("DEBUG:Called my_run")
            raise Exception('Run failed')

        with MonkeyPatch().context() as ctx:
            with pytest.raises(Exception):
                builtins.__import__ = myimport
                import wx
                ctx.setattr(wx, 'VERSION', (4, 0, 0, '', ''))
                ctx.setattr(robotide, '_run', my_run)
                result = robotide.main()
                print(f"DEBUG: RESULT= {result}")
                assert result.startswith('v2.0')

    def test_dialog_with_old_version(self):
        import robotide.application
        import wx

        def my_show(*args):
            print("DEBUG:Called my_show")

        with MonkeyPatch().context() as m:
            m.setattr(wx, 'VERSION', (4, 0, 0, '', ''))
            from wx import MessageDialog
            m.setattr(MessageDialog, 'ShowModal', my_show)
            robotide._show_old_wxpython_warning_if_needed()

    def test_dialog_with_new_version(self):
        import robotide.application
        import wx

        def my_show(*args):
            print("DEBUG:Called my_show")

        with MonkeyPatch().context() as m:
            m.setattr(wx, 'VERSION', (4, 4, 0, '', ''))
            from wx import MessageDialog
            m.setattr(MessageDialog, 'ShowModal', my_show)
            robotide._show_old_wxpython_warning_if_needed()

    def test_replace_std_for_win(self):
        import robotide
        import sys

        with MonkeyPatch().context() as m:
            m.setattr(sys, 'executable', 'pythonw.exe')
            m.setattr(sys, 'stderr', None)
            m.setattr(sys, 'stdout', None)
            robotide._replace_std_for_win()


class TestMisc(unittest.TestCase):

    def test_get_code(self):
        import wx
        from robotide.application import RIDE

        main_app = RIDE()
        code = main_app._get_language_code()
        assert code in (wx.LANGUAGE_ENGLISH, wx.LANGUAGE_ENGLISH_WORLD, wx.LANGUAGE_PORTUGUESE)


if __name__ == '__main__':
    unittest.main()
