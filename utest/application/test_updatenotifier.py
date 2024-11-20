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
import pytest
import sys
import typing
import unittest
import time
import urllib

from robotide.application.updatenotifier import UpdateNotifierController, UpdateDialog

IS_WINDOWS = sys.platform=='win32'

CHECKFORUPDATES = 'check for updates'
LASTUPDATECHECK = 'last update check'

import wx
from wx.lib.agw.aui import AuiManager
import wx.lib.agw.aui as aui
from multiprocessing import shared_memory
from utest.resources import datafilereader, MessageRecordingLoadObserver
from robotide.ui.mainframe import ActionRegisterer, ToolBar
from robotide.ui.actiontriggers import MenuBar, ShortcutRegistry
from robotide.application import Project
from utest.resources import FakeSettings
from robotide.publish import PUBLISHER
from robotide.ui.treeplugin import Tree
from robotide.ui.notebook import NoteBook
from robotide.editor import texteditor
from robotide.namespace.namespace import Namespace

app = wx.App()
nb_style = aui.AUI_NB_DEFAULT_STYLE | aui.AUI_NB_WINDOWLIST_BUTTON | aui.AUI_NB_TAB_EXTERNAL_MOVE \
           | aui.AUI_NB_SUB_NOTEBOOK | aui.AUI_NB_SMART_TABS
MYTESTOVERRIDE = 'My Overriding Test Teardown'


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
    book = None
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
        # self.settings.add_section("Text Edit")
        self.namespace = Namespace(self.settings)
        self.book = NoteBook(self.frame, self, nb_style)
        self._mgr = aui.AuiManager()

        # tell AuiManager to manage this frame
        self._mgr.SetManagedWindow(self.frame)
        self.book.SetBackgroundColour((255, 255, 255))
        self.book.SetForegroundColour((0, 0, 0))
        self._mgr.AddPane(self.book,
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


class UpdateNotifierTestCase(unittest.TestCase):

    def setUp(self):
        self._callback_called = False
        self._newest_version = None
        self._url = None
        self.app = MyApp()
        settings = self.app.settings
        self.frame = self.app.frame
        self.frame.actions = ActionRegisterer(AuiManager(self.frame), MenuBar(self.frame), ToolBar(self.frame),
                                              ShortcutRegistry(self.frame))
        self.frame.tree = Tree(self.frame, self.frame.actions, settings)
        self.app.project = Project(self.app.namespace, self.app.settings)
        self.plugin = texteditor.TextEditorPlugin(self.app)
        self.app.project.load_datafile(datafilereader.SIMPLE_PROJECT, MessageRecordingLoadObserver())
        self.notebook = self.app.book
        self.app.tree.populate(self.app.project)
        self.source = self.app.tree.controller
        self.app.frame.SetStatusText("File:" + self.app.project.data.source)
        # Uncomment next line (and MainLoop in tests) if you want to see the app
        # self.frame.Show()

    def tearDown(self):
        self.plugin.unsubscribe_all()
        PUBLISHER.unsubscribe_all()
        self.app.project.close()
        # wx.CallAfter(self.app.ExitMainLoop)
        # self.app.MainLoop()  # With this here, there is no Segmentation fault
        # wx.CallAfter(wx.Exit)
        self.app.Destroy()
        self.app = None


    def _callback(self, version, url, settings, notebook):
        __ = notebook
        self.assertFalse(self._callback_called)
        self._callback_called = True
        self.assertIsNotNone(version)
        self._newest_version = version
        self.assertIsNotNone(url)
        self._url = url
        self.assertEqual(dict, type(settings))

    @staticmethod
    def _update_notifier_controller(settings, notebook, current, new, url='some url'):
        ctrl = UpdateNotifierController(settings, notebook)
        ctrl.VERSION = current
        def _new():
            return new
        ctrl._get_newest_version = _new
        def _url():
            return url
        ctrl._get_download_url = _url
        def _null():
            return None
        ctrl._get_rf_pypi_data = _null
        return ctrl

    @staticmethod
    def internal_settings(check_for_updates: typing.Union[bool, None] = True,
                          last_update_check: typing.Union[float, None] = time.time() - 60 * 60 * 24 * 7 - 1):
        return {CHECKFORUPDATES: check_for_updates,
                LASTUPDATECHECK: last_update_check}

    def test_normal_update(self):
        settings = self.internal_settings()
        ctrl = self._update_notifier_controller(settings, self.notebook, '0', '1', 'http://xyz.abc.efg.di')
        ctrl.notify_update_if_needed(self._callback)
        self.assertTrue(self._callback_called)
        self.assertEqual('1', self._newest_version)
        self.assertEqual('http://xyz.abc.efg.di', self._url)
        self.assertTrue(settings[CHECKFORUPDATES])
        self.assertGreater(settings[LASTUPDATECHECK], time.time() - 1)
        # Uncomment next lines if you want to see the app
        # wx.CallLater(5000, self.app.ExitMainLoop)
        # self.app.MainLoop()

    def test_update_when_trunk_version(self):
        settings = self.internal_settings()
        ctrl = self._update_notifier_controller(settings, self.notebook, '2.0', '2.0.1')
        ctrl.notify_update_if_needed(self._callback)
        self.assertTrue(self._callback_called)
        self.assertEqual('2.0.1', self._newest_version)
        self.assertTrue(settings[CHECKFORUPDATES])
        self.assertGreater(settings[LASTUPDATECHECK], time.time() - 1)

    def test_last_update_done_less_than_a_week_ago(self):
        original_time = time.time() - 60 * 60 * 24 * 3
        settings = self.internal_settings(last_update_check=original_time)
        ctrl = UpdateNotifierController(settings, self.notebook)
        ctrl.notify_update_if_needed(self._callback)
        self.assertTrue(settings[CHECKFORUPDATES])
        self.assertEqual(original_time, settings[LASTUPDATECHECK])
        self.assertFalse(self._callback_called)

    def test_check_for_updates_is_false(self):
        settings = self.internal_settings(check_for_updates=False)
        original_time = settings[LASTUPDATECHECK]
        ctrl = UpdateNotifierController(settings, self.notebook)
        ctrl.notify_update_if_needed(self._callback)
        self.assertFalse(settings[CHECKFORUPDATES])
        self.assertEqual(original_time, settings[LASTUPDATECHECK])
        self.assertFalse(self._callback_called)

    def test_no_update_found(self):
        settings = self.internal_settings()
        ctrl = self._update_notifier_controller(settings, self.notebook, '0.55', '0.55')
        ctrl.notify_update_if_needed(self._callback)
        self.assertGreater(settings[LASTUPDATECHECK], time.time() - 1)
        self.assertFalse(self._callback_called)

    def test_no_update_found_dev(self):
        settings = self.internal_settings()
        ctrl = self._update_notifier_controller(settings, self.notebook, '0.56', '0.56')
        ctrl.notify_update_if_needed(self._callback, ignore_check_condition=False, show_no_update=False)
        self.assertGreater(settings[LASTUPDATECHECK], time.time() - 1)
        self.assertFalse(self._callback_called)

    @pytest.mark.skipif(IS_WINDOWS, reason='Causes: Windows fatal exception: access violation')
    def test_no_update_found_dev_notify(self):
        settings = self.internal_settings()
        ctrl = self._update_notifier_controller(settings, self.notebook, '0.55', '0.55')
        ctrl.notify_update_if_needed(self._callback, ignore_check_condition=True, show_no_update=True)
        self.assertFalse(self._callback_called)

    def test_first_run_sets_settings_correctly_and_checks_for_updates(self):
        settings = self.internal_settings(check_for_updates=None, last_update_check=None)
        ctrl = self._update_notifier_controller(settings, self.notebook,'1.0.2', '1.0.2')
        ctrl.notify_update_if_needed(self._callback)
        self.assertGreater(settings[LASTUPDATECHECK], time.time() - 1)
        self.assertTrue(settings[CHECKFORUPDATES])
        self.assertFalse(self._callback_called)

    def test_first_run_sets_settings_correctly_and_finds_an_update(self):
        settings = self.internal_settings(check_for_updates=None, last_update_check=None)
        ctrl = self._update_notifier_controller(settings, self.notebook, '1.2', '2.0')
        ctrl.notify_update_if_needed(self._callback)
        self.assertGreater(settings[LASTUPDATECHECK], time.time() - 1)
        self.assertTrue(settings[CHECKFORUPDATES])
        self.assertTrue(self._callback_called)

    def test_checking_timeouts(self):
        settings = self.internal_settings()
        ctrl = UpdateNotifierController(settings, self.notebook)

        def throw_timeout_error():
            raise urllib.error.URLError('timeout')

        ctrl._get_newest_version = throw_timeout_error
        ctrl.notify_update_if_needed(self._callback)
        self.assertGreater(settings[LASTUPDATECHECK], time.time() - 10)  # The dialog timeout in 10 seconds
        self.assertFalse(self._callback_called)

    def test_download_url_checking_timeouts(self):
        settings = self.internal_settings()
        ctrl = UpdateNotifierController(settings, self.notebook)
        ctrl.VERSION = '0'
        ctrl._get_newest_version = lambda: '1'

        def throw_timeout_error(*args):
            _ = args
            raise urllib.error.URLError('timeout')

        ctrl._get_download_url = throw_timeout_error
        ctrl.notify_update_if_needed(self._callback)
        self.assertGreater(settings[LASTUPDATECHECK], time.time() - 1)
        self.assertFalse(self._callback_called)

    def test_server_returns_no_versions(self):
        settings = self.internal_settings()
        ctrl = self._update_notifier_controller(settings, self.notebook, '1.2.2', None)
        ctrl.notify_update_if_needed(self._callback)
        self.assertGreater(settings[LASTUPDATECHECK], time.time() - 1)
        self.assertTrue(settings[CHECKFORUPDATES])
        self.assertFalse(self._callback_called)

    def test_server_returns_older_version(self):
        settings = self.internal_settings()
        ctrl = self._update_notifier_controller(settings, self.notebook, '0.44', '0.43.1')
        ctrl.notify_update_if_needed(self._callback)
        self.assertGreater(settings[LASTUPDATECHECK], time.time() - 1)
        self.assertTrue(settings[CHECKFORUPDATES])
        self.assertFalse(self._callback_called)

    @pytest.mark.skipif(IS_WINDOWS, reason='Causes: Windows fatal exception: access violation')
    def test_forced_check_released(self):
        settings = self.internal_settings()
        ctrl = self._update_notifier_controller(settings, self.notebook, '0.43.0', '0.43.1')
        ctrl.notify_update_if_needed(self._callback, ignore_check_condition=True)
        self.assertGreater(settings[LASTUPDATECHECK], time.time() - 19)  # The dialog timeout in 20 seconds
        self.assertTrue(settings[CHECKFORUPDATES])
        self.assertTrue(self._callback_called)

    @pytest.mark.skipif(IS_WINDOWS, reason='Causes: Windows fatal exception: access violation')
    def test_forced_check_development(self):
        settings = self.internal_settings()
        ctrl = self._update_notifier_controller(settings, self.notebook, '0.44dev12', '0.44.dev14')
        ctrl.notify_update_if_needed(self._callback, ignore_check_condition=True)
        self.assertGreater(settings[LASTUPDATECHECK], time.time() - 20)  # The dialog timeout in 20 seconds
        self.assertTrue(settings[CHECKFORUPDATES])
        self.assertTrue(self._callback_called)

    @pytest.mark.skipif(IS_WINDOWS, reason='Causes: Windows fatal exception: access violation')
    def test_forced_check_development_ok(self):
        settings = self.internal_settings()
        ctrl = self._update_notifier_controller(settings, self.notebook, '0.44dev12', '0.44.dev12')
        ctrl.notify_update_if_needed(self._callback, ignore_check_condition=False)
        self.assertGreater(settings[LASTUPDATECHECK], time.time() - 20)  # The dialog timeout in 20 seconds
        self.assertTrue(settings[CHECKFORUPDATES])
        self.assertFalse(self._callback_called)

    @pytest.mark.skipif(IS_WINDOWS, reason='Causes: Windows fatal exception: access violation')
    def test_normal_update_dialog(self):
        """ This is not actually doing a test """
        settings = self.internal_settings()
        ctrl=UpdateDialog('1.0.0', 'http://localhost', settings, self.notebook,False)
        wx.CallLater(3000, ctrl.EndModal,wx.CANCEL)
        ctrl.ShowModal()
        ctrl.Destroy()


if __name__ == '__main__':
    unittest.main()
