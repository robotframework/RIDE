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
import wx
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
from robotide.publish import PUBLISHER, RideSuiteAdded
from robotide.ui.treeplugin import Tree
from robotide.ui.notebook import NoteBook
from robotide.editor import texteditor
from robotide.namespace.namespace import Namespace

"""
th.FakeDirectorySuiteHandler = th.FakeUserKeywordHandler = \
    th.FakeSuiteHandler = th.FakeTestCaseHandler = \
    th.FakeResourceHandler = th.TestDataDirectoryHandler
st.Editor = lambda *args: FakeEditor()
"""
"""
DEBUG: 
Tree._show_correct_editor = lambda self, x: None
Tree.get_active_datafile = lambda self: None
Tree._select = lambda self, node: self.SelectItem(node)
Tree.get_selected_datafile_controller = lambda self, node: self.SelectItem(node)
"""
# app = wx.App()
nb_style = aui.AUI_NB_DEFAULT_STYLE | aui.AUI_NB_WINDOWLIST_BUTTON | aui.AUI_NB_TAB_EXTERNAL_MOVE \
           | aui.AUI_NB_SUB_NOTEBOOK | aui.AUI_NB_SMART_TABS


class MainFrame(wx.Frame):
    book = None

    def __init__(self):
        wx.Frame.__init__(self, parent=None, title='Text Editor Test App')

        self.CreateStatusBar()
        # self.SetStatusText("wxPython " + wx.version())

        # self.book = Notebook(self, )
        # panel = wx.Panel(book)
        # for i in range(2):
        #    panel = wx.Panel(book)
        #    book.InsertPage(i, panel, "Page #" + str(i + 1))


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

    def OnInit(self):
        self.frame = MainFrame()
        self.SetTopWindow(self.frame)
        self.settings = FakeSettings()
        self.settings.add_section("Text Edit")
        self.namespace = Namespace(self.settings)
        self.book = NoteBook(self.frame, self, nb_style)
        # self.book = self.frame.book
        # self.panel = wx.Panel(self.book)
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
        # self.SetToolBar(self.toolbar.GetToolBar())
        mb._frame.SetBackgroundColour((255, 255, 255))
        mb._frame.SetForegroundColour((0, 0, 0))
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
        # mb.register("File|Open")
        mb.take_menu_bar_into_use()
        self._mgr.Update()
        return True


class TestEditorCommands(unittest.TestCase):

    def setUp(self):
        self.app = MyApp()
        settings = self.app.settings
        self.frame = self.app.frame
        self.frame.tree = Tree(self.frame, ActionRegisterer(AuiManager(self.frame),
                                                            MenuBar(self.frame), ToolBar(self.frame),
                                                            ShortcutRegistry(self.frame)), settings)
        self.app.project = Project(self.app.namespace, self.app.settings)
        self.plugin = texteditor.TextEditorPlugin(self.app)
        self.plugin._editor_component = texteditor.SourceEditor(self.app.book, "Text Edit",
                                                                texteditor.DataValidationHandler(self.plugin))
        self.plugin.enable()
        self.app.project.load_datafile(datafilereader.TESTCASEFILE_WITH_EVERYTHING, MessageRecordingLoadObserver())
        self.app.tree.set_editor(self.plugin._editor_component)
        self.app.tree.populate(self.app.project)
        self.frame.Show()

    def tearDown(self):
        self.plugin.unsubscribe_all()
        PUBLISHER.unsubscribe_all()
        self.app.project.close()
        wx.CallAfter(self.app.ExitMainLoop)
        self.app.MainLoop()  # With this here, there is no Segmentation fault
        # wx.CallAfter(wx.Exit)
        self.app.Destroy()
        self.app = None

    def test_insert_row_single(self):
        self.app.project.load_datafile(datafilereader.TESTCASEFILE_WITH_EVERYTHING, MessageRecordingLoadObserver())
        print(f"DEBUG: project source={self.app.project.data.source} plugin={self.plugin.name}")
        # assert
        # self.app.book.InsertPage(0, self.app.panel, "Text Edit")
        # self.editor._open()
        # self.plugin._editor.open(self.app.project.data.data)
        print(f"DEBUG: project is_focused={self.plugin._editor.is_focused()} plugin enabled? "
              f"{self.plugin.initially_enabled}")
        # self.plugin.OnOpen(None)
        print(f"DEBUG: project datafile={self.plugin.get_selected_datafile()}")
        print(f"DEBUG: selected datafile_controller={self.app.tree.get_selected_datafile_controller()}")
        item = self.app.tree.GetFirstVisibleItem()
        print(f"DEBUG: tree first item={item}")
        # self.plugin._editor.open(self.app.project._controller)
        self.plugin._open_tree_selection_in_editor()
        self.plugin._editor._editor.SetFocus()
        self.plugin._editor._editor.SetText("Hello World!")
        self.plugin._editor.insert_row(None)
        fulltext = self.plugin._editor._editor.GetText()
        datafile_controller = self.plugin.tree.get_selected_datafile_controller()
        print(f"DEBUG: tree datafile_controller={datafile_controller}")
        print(f"DEBUG: project Fulltext={fulltext}")
        # editor.open(self.app.project._controller)
        # editor.open(self.app.project.data)
        # editor.
        self.app.frame.SetStatusText("File: " + self.app.project.data.source)
        # Uncomment next lines if you want to see the app
        # wx.CallLater(5000, self.app.ExitMainLoop)
        # self.app.MainLoop()


if __name__ == '__main__':
    unittest.main()

