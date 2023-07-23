#  Copyright 2008-2015 Nokia Networks
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
import pathlib
import tempfile
import unittest
from wx.lib.agw.aui import AuiManager
import wx.lib.agw.aui as aui
from functools import total_ordering
from robotide.ui.tagdialogs import ViewAllTagsDialog
from utest.resources import datafilereader, MessageRecordingLoadObserver
from robotide.robotapi import (TestDataDirectory, TestCaseFile, ResourceFile,
                               TestCase, UserKeyword)
from robotide.spec.librarymanager import LibraryManager
from robotide.ui.mainframe import ActionRegisterer, ToolBar
from robotide.ui.actiontriggers import MenuBar, ShortcutRegistry
from robotide.application import Project
from robotide.controller.filecontrollers import (TestDataDirectoryController,
                                                 ResourceFileController)
from robotide import utils
from utest.resources import FakeSettings, FakeEditor
# from robotide.ui import treeplugin as st
# from robotide.ui import treenodehandlers as th
from robotide.publish import PUBLISHER, RideSuiteAdded, RideNotebookTabChanging
from robotide.ui.treeplugin import Tree
from robotide.ui.notebook import NoteBook
from robotide.editor import kweditor
from robotide.editor.gridbase import GridEditor
from robotide.namespace.namespace import Namespace

import os
import pytest
DISPLAY = os.getenv('DISPLAY')
if not DISPLAY: # Avoid failing unit tests in system without X11
    pytest.skip("Skipped because of missing DISPLAY", allow_module_level=True)
import wx
import shutil
import sys
from mockito import mock

from robotide.robotapi import Variable
from robotide.controller import data_controller
from robotide.controller.robotdata import new_test_case_file
from robotide.controller.settingcontrollers import VariableController
from robotide.controller.tablecontrollers import VariableTableController
from robotide.editor import EditorPlugin, EditorCreator
from robotide.editor.kweditor import KeywordEditor
from robotide.editor.editors import TestCaseFileEditor, WelcomePage
from robotide.editor.macroeditors import TestCaseEditor
from robotide.preferences import RideSettings
from robotide.namespace import Namespace
from utest.resources import FakeSettings
# Workaround for relative import in non-module
# see https://stackoverflow.com/questions/16981921/relative-imports-in-python-3
PACKAGE_PARENT = '..'
SCRIPT_DIR = os.path.dirname(os.path.realpath(os.path.join(os.getcwd(),
                                              os.path.expanduser(__file__))))
sys.path.append(os.path.normpath(os.path.join(SCRIPT_DIR, PACKAGE_PARENT)))
try:
    from fakeplugin import FakePlugin
except ImportError:  # Python 3
    from .fakeplugin import FakePlugin

"""
PACKAGE_PARENT = '../controller'
SCRIPT_DIR = os.path.dirname(os.path.realpath(os.path.join(os.getcwd(),
                                              os.path.expanduser(__file__))))
sys.path.append(os.path.normpath(os.path.join(SCRIPT_DIR, PACKAGE_PARENT)))

from ..controller.controller_creator import testcase_controller
"""

DATADIR = 'fake'
DATAPATH = '%s/path' % DATADIR
TestCaseFileEditor._populate = lambda self: None

"""
app = mock(RIDE(path=None, updatecheck=False))
frame = wx.Frame(parent=None, title='Test Frame')
app.frame = frame
app.namespace = mock(Namespace)
app.settings = FakeSettings()
app.register_editor()
"""
# frame.Show()
nb_style = aui.AUI_NB_DEFAULT_STYLE | aui.AUI_NB_WINDOWLIST_BUTTON | aui.AUI_NB_TAB_EXTERNAL_MOVE \
           | aui.AUI_NB_SUB_NOTEBOOK | aui.AUI_NB_SMART_TABS


class MainFrame(wx.Frame):
    notebook = None

    def __init__(self):
        wx.Frame.__init__(self, parent=None, title='Grid Editor Test App')

        self.CreateStatusBar()


class MyApp(wx.App):
    frame = None
    namespace = None
    project = None
    settings = None
    # notebook = None
    panel = None
    plugin = None
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
        _, self.file_settings = tempfile.mkstemp('.cfg', text=True)
        self.global_settings = RideSettings(self.file_settings)
        self.global_settings.add_section("Grid")
        self.settings.global_settings = self.global_settings
        self.settings.add_section("Grid")
        self.namespace = Namespace(self.global_settings)
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
        # self.SetToolBar(self.toolbar.GetToolBar())
        mb.m_frame.SetBackgroundColour((255, 255, 255))
        mb.m_frame.SetForegroundColour((0, 0, 0))
        self._mgr.AddPane(self.toolbar, aui.AuiPaneInfo().Name("maintoolbar").
                          ToolbarPane().Top())
        self.actions = ActionRegisterer(self._mgr, mb, self.toolbar,
                                        ShortcutRegistry(self.frame))
        self.tree = Tree(self.frame, self.actions, self.settings)
        self.tree.SetMinSize(wx.Size(275, 250))
        self.frame.SetMinSize(wx.Size(600, 400))
        self._mgr.AddPane(self.tree,
                          aui.AuiPaneInfo().Name("tree_content").Caption("Test Suites").CloseButton(False).
                          LeftDockable())
        # self.plugin = kweditor.KeywordEditor(self, self._datafile_controller(), self.tree)
        # mb.register("File|Open")
        mb.take_menu_bar_into_use()
        self._mgr.Update()
        return True

    def _datafile_controller(self):
        return data_controller(new_test_case_file(datafilereader.TESTCASEFILE_WITH_EVERYTHING), None)

    def OnExit(self):  # Overrides wx method
        os.remove(self.file_settings)


class KeywordEditorTest(unittest.TestCase):

    def setUp(self):
        self.app = MyApp()
        settings = self.app.settings
        self.frame = self.app.frame
        self.frame.tree = Tree(self.frame, ActionRegisterer(AuiManager(self.frame),
                                                            MenuBar(self.frame), ToolBar(self.frame),
                                                            ShortcutRegistry(self.frame)), settings)
        self.app.project = Project(self.app.namespace, self.app.settings)
        self._registered_editors = {}
        self.creator = EditorCreator(self._register)
        self.creator.register_editors()

        # self.plugin = self._datafile_plugin(self.app)
        # self.plugin = kweditor.KeywordEditor(self.app, self.frame.tree)
        # self.plugin._editor_component = kweditor.ContentAssistCellEditor()
        """
        texteditor.SourceEditor(self.app.notebook, self.plugin.title,
                                                                texteditor.DataValidationHandler(self.plugin))
        """
        self.frame.notebook = self.app.notebook
        self.plugin = EditorPlugin(self.app)
        self.plugin.title = 'Editor'
        self._test = self._datafile_controller()  # testcase_controller()
        self._panel = wx.Panel(self.app.frame)
        sizer = wx.BoxSizer()
        self._grid = GridEditor(self._panel, 10, 6).SetSizer(sizer=sizer)
        # self.editor = TestCaseEditor(self.app, self._grid, self._test, self.app.tree)
        # self.plugin._editor_component = KeywordEditor(self.plugin, self.editor, self.app.tree)

        # self.editor = self._datafile_editor()
        # self.editor = self.plugin.get_editor(TestCase)
        # Moved to test
        # self.plugin.enable()
        self.app.project.load_datafile(datafilereader.TESTCASEFILE_WITH_EVERYTHING, MessageRecordingLoadObserver())
        # self.app.tree.set_editor(self.plugin._editor_component)
        self.app.tree.populate(self.app.project)
        self.app.frame.SetStatusText("File:" + self.app.project.data.source)
        # Uncomment next line (and MainLoop in tests) if you want to see the app
        self.frame.Show()

    def _register(self, iclass, eclass):
        self._registered_editors[iclass] = eclass

    def _editor_for(self, plugin):
        return self.creator.editor_for(plugin, self.frame, None)

    def _datafile_editor(self):
        return self.creator.editor_for(self._datafile_plugin(self.app), self.frame, None)

    def _datafile_plugin(self, parent):
        # return FakePlugin(self._registered_editors, self._datafile_controller())
        print(f"DEBUG: _datafile_plugin parent={parent}")
        return TestCaseEditor(self.plugin, self._grid, self._datafile_controller(), self.frame.tree)

    def _variable_plugin(self):
        return FakePlugin(self._registered_editors,
                          VariableController(VariableTableController(
                              self._datafile_controller(), None),
                              Variable(None, '','')))

    def _no_item_selected_plugin(self):
        return FakePlugin(self._registered_editors, None)

    def _datafile_controller(self):
        return data_controller(new_test_case_file(datafilereader.TESTCASEFILE_WITH_EVERYTHING), None)

    def tearDown(self):
        self.plugin.unsubscribe_all()
        PUBLISHER.unsubscribe_all()
        self.app.project.close()
        wx.CallAfter(self.app.ExitMainLoop)
        # self.app.MainLoop()  # With this here, there is no Segmentation fault
        # wx.CallAfter(wx.Exit)
        self.app.Destroy()
        self.app = None
        if os.path.exists(DATADIR):
            shutil.rmtree(DATADIR, ignore_errors=True)

    """
    def test_enable(self):
        self.plugin.enable()

    def test_is_focused(self):
        focused = self.plugin.is_focused()
        assert focused is True
        wx.CallLater(5000, self.app.ExitMainLoop)
        self.app.MainLoop()
    """

    """
    def test_highlight_cell(self):
        highlight = self.plugin.highlight_cell('None')
        assert highlight is True

    def test_disable(self):
        self.plugin.disable()
    """

    def test_show(self):
        show = self.creator.editor_for(self.plugin, self._panel, self.frame.tree)
        print(f"DEBUG: Editor is {show}")
        assert show is not None


if __name__ == '__main__':
    unittest.main()
