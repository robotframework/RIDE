#  Copyright 2025-     Robot Framework Foundation
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
import os
import pytest
import sys
import unittest
from pytest import MonkeyPatch
import wx
import wx.lib.agw.aui as aui
from wx.core import wxEVT_COMMAND_MENU_SELECTED

from robotide.ui.mainframe import ActionRegisterer, ToolBar
from robotide.ui.actiontriggers import MenuBar, ShortcutRegistry
from utest.resources import FakeSettings
from robotide.ui.treeplugin import Tree
from robotide.ui.notebook import NoteBook
from robotide.namespace.namespace import Namespace
from robotide.postinstall import MessageDialog

IS_WINDOWS = sys.platform=='win32'

CHECKFORUPDATES = 'check for updates'
LASTUPDATECHECK = 'last update check'

app = wx.App()
nb_style = aui.AUI_NB_DEFAULT_STYLE | aui.AUI_NB_WINDOWLIST_BUTTON | aui.AUI_NB_TAB_EXTERNAL_MOVE \
           | aui.AUI_NB_SUB_NOTEBOOK | aui.AUI_NB_SMART_TABS
MYTESTOVERRIDE = 'My Overriding Test Teardown'


class TestVerifyInstall(unittest.TestCase):

    @pytest.mark.order(3)
    def test_valid_verify(self):
        from robotide.postinstall import verify_install
        result = verify_install()
        assert result


class MainFrame(wx.Frame):
    book = None

    def __init__(self):
        wx.Frame.__init__(self, parent=None, title='Test App')

        self.CreateStatusBar()


class MyApp(wx.App):
    frame = None
    namespace = None
    project = None
    settings = None
    notebook = None
    panel = None
    tree = None

    def __init__(self, redirect=False, filename=None, usebestvisual=False, clearsigint=True):
        super().__init__(redirect, filename, usebestvisual, clearsigint)
        self.actions = None
        self.toolbar = None
        self._mgr = None

    def OnInit(self):  # Overrides wx method
        self.frame = MainFrame()
        self.SetTopWindow(self.frame)
        self.settings = FakeSettings()
        self.namespace = Namespace(self.settings)
        self.notebook = NoteBook(self.frame, self, nb_style)
        self._mgr = aui.AuiManager()

        # tell AuiManager to manage this frame
        self._mgr.SetManagedWindow(self.frame)
        self.notebook.SetBackgroundColour((255, 255, 255))
        self.notebook.SetForegroundColour((0, 0, 0))
        self._mgr.AddPane(self.notebook,
                          aui.AuiPaneInfo().Name("notebook_editors").
                          CenterPane().PaneBorder(False))
        mb = MenuBar(self.frame)
        self.toolbar = ToolBar(self.frame)
        self.toolbar.SetMinSize(wx.Size(100, 60))
        self.toolbar.SetBackgroundColour((255, 255, 255))
        self.toolbar.SetForegroundColour((0, 0, 0))
        mb.m_frame.SetBackgroundColour((255, 255, 255))
        mb.m_frame.SetForegroundColour((0, 0, 0))
        self._mgr.AddPane(self.toolbar, aui.AuiPaneInfo().Name("maintoolbar").
                          ToolbarPane().Top())
        self.frame.actions = ActionRegisterer(self._mgr, mb, self.toolbar, ShortcutRegistry(self.frame))
        self.tree = Tree(self.frame, self.frame.actions, self.settings)
        self.tree.SetMinSize(wx.Size(275, 250))
        self.frame.SetMinSize(wx.Size(600, 400))
        self._mgr.AddPane(self.tree,
                          aui.AuiPaneInfo().Name("tree_content").Caption("Test Suites").CloseButton(False).
                          LeftDockable())
        mb.take_menu_bar_into_use()
        self._mgr.Update()
        return True


class MyModalDialogHook(wx.ModalDialogHook):

    def __init__(self, result):
        wx.ModalDialogHook.__init__(self)
        self.result = result

    def Enter(self, dialog):
        if isinstance(dialog, (wx.DirDialog, MessageDialog)):
            return self.result
        # Allow the dialog to be shown as usual.
        return wx.ID_NONE


class MessageDialogTestCase(unittest.TestCase):

    def test_ask_yes_no_no_frame(self):
        from robotide.postinstall import _askyesno

        title = "MessageDialog Test"
        msg= "Testing Dialog, frame and no_default with defaults"
        result = _askyesno(title, msg)
        print(f"DEBUG: test_ask_yes_no_no_frame result={result}")
        assert not result

    def test_ask_yes_no_frame(self):
        self.app = MyApp()
        self.frame = self.app.frame
        self.frame.Show()
        from robotide.postinstall import _askyesno

        title = "MessageDialog Test"
        msg= "Testing Dialog, with frame and no_default with default"
        result = _askyesno(title, msg, frame=self.frame)
        print(f"DEBUG: test_ask_yes_no_frame result={result}")
        assert not result

    def test_ask_yes_no_no_frame_and_no_default(self):
        from robotide.postinstall import _askyesno
        title = "MessageDialog Test"
        msg = "Testing Dialog, no frame and no_default True"
        result = _askyesno(title, msg, no_default=True)
        print(f"DEBUG: test_ask_yes_no_no_frame_and_no_default result={result}")
        assert not result

    def test_ask_yes_no_frame_ok(self):
        self.app = MyApp()
        self.frame = self.app.frame
        self.frame.Show()
        from robotide.postinstall import _askyesno
        self.myHook = MyModalDialogHook(wx.ID_OK)  # wx.ID_YES
        self.myHook.Register()
        title = "MessageDialog Test"
        msg= "Testing Dialog, with frame and OK"
        result = _askyesno(title, msg, frame=self.frame)
        print(f"DEBUG: test_ask_yes_no_frame_ok result={result}")
        assert result

    def test_ask_yes_no_frame_cancel(self):
        self.app = MyApp()
        self.frame = self.app.frame
        self.frame.Show()
        from robotide.postinstall import _askyesno
        self.myHook = MyModalDialogHook(wx.ID_CANCEL)
        self.myHook.Register()
        title = "MessageDialog Test"
        msg= "Testing Dialog, with frame and CANCEL"
        result = _askyesno(title, msg, frame=self.frame)
        print(f"DEBUG: test_ask_yes_no_frame_cancel result={result}")
        assert not result

    def test_ask_directory_no_frame_cancel(self):
        from robotide.postinstall import _askdirectory
        self.myHook = MyModalDialogHook(wx.ID_CANCEL)
        self.myHook.Register()
        title = "MessageDialog Test"
        initialdir = os.path.curdir
        result = _askdirectory(title, initialdir)
        assert result is None

    def test_ask_directory_frame_cancel(self):
        from robotide.postinstall import _askdirectory
        self.app = MyApp()
        self.frame = self.app.frame
        self.frame.Show()
        self.myHook = MyModalDialogHook(wx.ID_CANCEL)
        self.myHook.Register()
        title = "MessageDialog Test"
        initialdir = os.path.curdir
        result = _askdirectory(title, initialdir, frame=self.frame)
        assert result is None

    def test_ask_directory_frame_ok(self):
        from robotide.postinstall import _askdirectory
        self.app = MyApp()
        self.frame = self.app.frame
        self.frame.Show()
        self.myHook = MyModalDialogHook(wx.ID_OK)
        self.myHook.Register()
        title = "MessageDialog Test"
        initialdir = os.path.curdir
        result = _askdirectory(title, initialdir, frame=self.frame)
        print(f"DEBUG: test_ask_directory_frame_ok result={result}")
        assert result is not None

global option_f
from os import environ, getlogin
from os.path import exists, join
DEFAULT_LANGUAGE = environ.get('LANG', '').split(':')

def reset_shortcut():
    desktop = {"de": "Desktop", "en": "Desktop", "es": "Escritorio",
               "fi": r"Työpöytä", "fr": "Bureau", "it": "Scrivania",
               "pt": r"Área de Trabalho", "zh": "Desktop"}
    user = getlogin()
    ndesktop = desktop[DEFAULT_LANGUAGE[0][:2]]
    directory = join("/home", user, ndesktop)
    defaultdir = join("/home", user, "Desktop")
    if not exists(directory):
        if exists(defaultdir):
            directory = defaultdir
        else:
            directory = None
    try:
        link = join(directory, "RIDE.desktop")
    except UnicodeError:
        link = join(directory.encode('utf-8'), "RIDE.desktop")
    if exists(link):
        os.remove(link)

@pytest.mark.skipif(sys.platform != 'linux', reason="Test only for Linux")
class CreateShortcut(unittest.TestCase):

    # def setUp(self):
    #     reset_shortcut()

    def tearDown(self):
      reset_shortcut()

    def test_call_create_shortcut_no_frame(self):
        from robotide.postinstall import caller

        result = caller(None,'linux')  # We need to delete existing shortcut
        assert result is not None

        result = caller(None,'darwin')
        assert result is False

        result = caller(None,'win32')
        assert result is False

        result = caller(None, 'zxspectrum')
        assert result is False

    def test_call_create_shortcut_frame_linux_cancel(self):
        from robotide.postinstall import caller
        self.app = MyApp()
        self.frame = self.app.frame
        self.frame.Show()
        self.myHook = MyModalDialogHook(wx.ID_CANCEL)
        self.myHook.Register()
        global option_f
        result = caller(self.frame,'linux')  # We need to delete existing shortcut
        assert result is None

    def test_call_create_shortcut_no_frame_linux_cancel(self):
        import  robotide.postinstall
        from robotide.postinstall import caller, _create_desktop_shortcut_linux
        self.app = MyApp()
        self.frame = self.app.frame
        self.frame.Show()

        def side_effect(frame=None):
            global option_q
            global option_f
            option_q = False
            option_f = frame is not None
            print(f"DEBUG: side_effect Called with {option_q=} {option_f=}")
            return _create_desktop_shortcut_linux(frame)

        with MonkeyPatch().context() as m:
            m.setattr(robotide.postinstall, 'caller', side_effect)
            self.myHook = MyModalDialogHook(wx.ID_CANCEL)
            self.myHook.Register()
            result = caller(None, 'linux')
            assert result is False

    def test_call_create_shortcut_frame_linux_ok(self):
        import  robotide.postinstall
        from robotide.postinstall import caller, _create_desktop_shortcut_linux
        self.app = MyApp()
        self.frame = self.app.frame
        self.frame.Show()

        def side_effect(frame=None):
            global option_q
            global option_f
            option_q = False
            option_f = frame is not None
            print(f"DEBUG: side_effect Called with {option_q=} {option_f=}")
            return _create_desktop_shortcut_linux(frame)

        with MonkeyPatch().context() as m:
            m.setattr(robotide.postinstall, 'caller', side_effect)
            self.myHook = MyModalDialogHook(wx.ID_OK)
            self.myHook.Register()
            result = caller(self.frame, 'linux')
            assert result is None

    def test_main_install(self):
        from robotide.postinstall import main
        main('-help')
        main('-install')
        main('-remove')
        main('-f', '-q', '-install')


class ShortcutPluginTest(unittest.TestCase):

    def test_methods(self):
        import robotide.postinstall
        from robotide.postinstall import caller
        from robotide.postinstall import ShortcutPlugin
        self.app = MyApp()
        self.frame = self.app.frame
        self.frame.Show()

        myplugin = ShortcutPlugin(self.app)
        myplugin._close()
        myplugin.enable()
        myplugin._create_menu()

        def side_effect(frame=None, platform='linux'):
            global option_q
            global option_f
            option_q = False
            option_f = frame is not None
            print(f"DEBUG: side_effect Called with {option_q=} {option_f=} {platform=}")
            return True

        with MonkeyPatch().context() as m:
            m.setattr(robotide.postinstall, 'caller', side_effect)
            # myplugin.on_view_shortcut_create(None)
            myplugin.call_creator(self.app.notebook)

        myplugin.disable()


if __name__ == '__main__':
    unittest.main()
