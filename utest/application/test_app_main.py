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
import os.path
import sys
import unittest
import pytest
from pytest import MonkeyPatch
import builtins
import wx

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

    @pytest.mark.order(2)
    def test_postinstall_wx(self):  # This test passed in PyCharm but not when run in command line
        with MonkeyPatch().context() as m:
            with pytest.raises((ImportError, SystemExit)):  # (ImportError, ModuleNotFoundError, SystemExit)):
                sys.modules.pop('wx.Color', None)
                builtins.__import__ = myimport
                import robotide.postinstall
                from wx import Colour
                print(dir(robotide.postinstall), dir(Colour))

    @pytest.mark.order(3)
    def test_fail_verify(self):
        with MonkeyPatch().context() as m:
            with pytest.raises(SystemExit):
                sys.modules.pop('wx.version', None)
                builtins.__import__ = myimport
                from robotide.postinstall import verify_install
                result = verify_install()
                assert not result


builtins.__import__ = real_import


class TestMain(unittest.TestCase):

    def tearDown(self):
        builtins.__import__ = real_import

    @pytest.mark.skip("New main process uses sys.argv")
    def test_main_call_with_extra_args(self):
        from robotide import main
        with pytest.raises(SystemExit):
            main('--noupdatecheck', '--debugconsole', '--version', 'test.robot')

    @pytest.mark.skip("New main process uses sys.argv")
    def test_main_call_with_help(self):
        from robotide import main
        with pytest.raises(SystemExit):
            result = main('--noupdatecheck', '--debugconsole', '--help')
            assert result.startswith('usage: ride')

    @pytest.mark.skip("New main process uses sys.argv")
    def test_main_call_with_version(self):
        from robotide import main
        with pytest.raises(SystemExit):
            result = main('--version')
            print(f"DEBUG: Result is {result}")
            assert result.startswith('v2.')

    @pytest.mark.skip("New main process uses sys.argv")
    def test_main_call_with_fail_version(self):
        import robotide
        with (MonkeyPatch().context()):
            with pytest.raises((ImportError, SystemExit)):
                builtins.__import__ = myimport
                result = robotide.main('--version')  # Need to capture output
                assert result.startswith('v2.')

    """
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
    """

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

    @pytest.mark.skip("Test fails when run with invoke")
    def test_main_call_with_fail_run(self):
        import robotide

        def my_run(inpath=None, updatecheck=True, debug_console=False, settingspath=None):
            print("DEBUG:Called my_run, args:=inpath=None, updatecheck=True, debug_console=False, settingspath=None")
            raise Exception('Run failed')

        with MonkeyPatch().context() as ctx:
            with pytest.raises(Exception):
                builtins.__import__ = myimport
                import wx
                ctx.setattr(wx, 'VERSION', (4, 0, 0, '', ''))
                ctx.setattr(robotide, '_run', my_run)
                try:
                    result = robotide.main()
                except Exception as e:
                    raise e
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

    @pytest.mark.skipif(sys.platform != 'win32', reason="Test only for Windows")
    def test_replace_std_for_win(self):
        import robotide
        import sys

        with MonkeyPatch().context() as m:
            m.setattr(sys, 'executable', 'pythonw.exe')
            m.setattr(sys, 'stderr', None)
            m.setattr(sys, 'stdout', None)
            robotide._replace_std_for_win()
            sys.stdout.write('content')
            sys.stdout.writelines(['content', 'line two'])
            sys.stdout.flush()
            sys.stdout.close()


class TestMisc(unittest.TestCase):

    def setUp(self):
        from robotide.application import RIDE
        self.main_app = RIDE()
        self.settings = self.main_app.settings
        self.frame = self.main_app.frame
        self.main_app.SetExitOnFrameDelete(True)

    def tearDown(self):
        # builtins.__import__ = real_import
        self.main_app.ExitMainLoop()
        self.main_app.Destroy()
        self.main_app = None

    def test_get_code(self):
        code = self.main_app._get_language_code()
        assert code in (175, wx.LANGUAGE_ENGLISH_WORLD, wx.LANGUAGE_PORTUGUESE)

    @pytest.mark.skipif(sys.platform != 'win32', reason="Test only for Windows")
    def test_nullstream(self):
        import sys
        from robotide import _replace_std_for_win
        _replace_std_for_win()
        try:
            sys.stdout.write('content')
            sys.stdout.writelines(['content', 'line two'])
            sys.stdout.flush()
        except Exception:
            pass
        # finally:
        #    sys.stdout.close()


class TestFSWatcher(unittest.TestCase):

    def test_obj_fs_watcher(self):  # Renamed to run in last
        from robotide.utils.eventhandler import RideFSWatcherHandler, normalize_windows_path, IS_WINDOWS
        fs_watcher = RideFSWatcherHandler
        check_path = ('.\\A\\Windows\\Path', './a/windows/path') if IS_WINDOWS else ('./A/Linux/Path', './A/Linux/Path')
        assert check_path[1] == normalize_windows_path(check_path[0])
        fs_watcher.create_fs_watcher(__file__)
        fs_watcher.create_fs_watcher(__file__)
        fs_watcher.start_listening(__file__)
        fs_watcher.start_listening(os.path.dirname(__file__))
        assert fs_watcher.is_watcher_created()
        assert not fs_watcher.is_workspace_dirty()
        assert os.path.dirname(__file__) == fs_watcher.get_workspace_new_path()
        # print(f"DEBUG: test_fs_watcher get_workspace_new_path = {fs_watcher.get_workspace_new_path()}")
        fs_watcher.exclude_listening(__file__)
        fs_watcher.exclude_listening(os.path.dirname(__file__))
        fs_watcher.stop_listening()


if __name__ == '__main__':
    unittest.main()
