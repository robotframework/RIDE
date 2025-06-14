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

import unittest

from hgext.histedit import message
from wx.lib.agw.aui import AuiManager
import wx.lib.agw.aui as aui
from multiprocessing import shared_memory
from functools import total_ordering
from robotide.ui.tagdialogs import ViewAllTagsDialog
from utest.resources import datafilereader, MessageRecordingLoadObserver
from robotide.publish import PUBLISHER, RideExecuteLibraryInstall, RideOpenLibraryDocumentation
from robotide.spec.libraryfinder import LibraryFinderPlugin
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
from robotide.editor import texteditor
from robotide.namespace.namespace import Namespace

import os
import wx
import shutil
import sys
from mockito import mock

from robotide.robotapi import Variable
from robotide.controller import data_controller
from robotide.controller.robotdata import new_test_case_file
from robotide.controller.settingcontrollers import VariableController
from robotide.controller.tablecontrollers import VariableTableController
from robotide.editor import EditorPlugin
from robotide.editor.kweditor import KeywordEditor
from robotide.editor.editors import TestCaseFileEditor, WelcomePage
from robotide.editor.macroeditors import TestCaseEditor
from robotide.editor.customsourceeditor import SourceCodeEditor
from robotide.namespace import Namespace
from utest.resources import FakeSettings
# Workaround for relative import in non-module
# see https://stackoverflow.com/questions/16981921/relative-imports-in-python-3
PACKAGE_PARENT = '..'
SCRIPT_DIR = os.path.dirname(os.path.realpath(os.path.join(os.getcwd(),
                                              os.path.expanduser(__file__))))
sys.path.append(os.path.normpath(os.path.join(SCRIPT_DIR, PACKAGE_PARENT)))

DATADIR = 'fake'
DATAPATH = '%s/path' % DATADIR
TestCaseFileEditor._populate = lambda self: None

nb_style = aui.AUI_NB_DEFAULT_STYLE | aui.AUI_NB_WINDOWLIST_BUTTON | aui.AUI_NB_TAB_EXTERNAL_MOVE \
           | aui.AUI_NB_SUB_NOTEBOOK | aui.AUI_NB_SMART_TABS


class MainFrame(wx.Frame):
    notebook = None

    def __init__(self):
        wx.Frame.__init__(self, parent=None, title='Text Editor Test App')
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
        self.settings.add_section("Linary Finder")
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
        # mb.register("File|Open")
        mb.take_menu_bar_into_use()
        self._mgr.Update()
        return True

class TestLibraryFinder(unittest.TestCase):

    def setUp(self):
        self.app = MyApp()
        try:
            self.shared_mem = shared_memory.ShareableList(['en'], name="language")
        except FileExistsError:  # Other instance created file
            self.shared_mem = shared_memory.ShareableList(name="language")
        settings = self.app.settings
        self.frame = self.app.frame
        self.frame.actions = ActionRegisterer(AuiManager(self.frame), MenuBar(self.frame), ToolBar(self.frame),
                                              ShortcutRegistry(self.frame))
        self.frame.tree = Tree(self.frame, self.frame.actions, settings)
        self.app.project = Project(self.app.namespace, self.app.settings)

        self.plugin = LibraryFinderPlugin(self.app)
        # self.plugin._editor_component = texteditor.SourceEditor(self.plugin, self.app.notebook, self.plugin.title,
        #                                                         texteditor.DataValidationHandler(self.plugin, lang='en'))
        self.plugin._editor_component = SourceCodeEditor(self.frame, options={'tab markers': True, 'fold symbols': 2})
        self.frame.notebook = self.app.notebook

        self.plugin.enable()
        self.app.project.load_datafile(datafilereader.TESTCASEFILE_WITH_EVERYTHING, MessageRecordingLoadObserver())
        self.app.tree.set_editor(self.plugin._editor_component)
        self.app.tree.populate(self.app.project)
        self.app.frame.SetStatusText("File:" + self.app.project.data.source)
        self.suite = self.app.project.data.suites
        self.imports = [i for i in self.suite]  # .imports
        self.plugin.get_selected_item()
        # Uncomment next line (and MainLoop in tests) if you want to see the app
        self.frame.Show()

    def tearDown(self):
        self.plugin.disable()
        self.plugin.unsubscribe_all()
        PUBLISHER.unsubscribe_all()
        self.app.project.close()
        wx.CallAfter(self.app.ExitMainLoop)
        # self.app.MainLoop()  # With this here, there is no Segmentation fault
        # wx.CallAfter(wx.Exit)
        self.shared_mem.shm.close()
        self.shared_mem.shm.unlink()
        self.app.Destroy()
        self.app = None
        if os.path.exists(DATADIR):
            shutil.rmtree(DATADIR, ignore_errors=True)

    def test_call_plugin_exec_install(self):
        print(f"DEBUG: test_libraryfinder.py test_call_plugin_exec_install imports={self.imports}")
        msg = RideExecuteLibraryInstall(item=None)
        # self.plugin._ps_on_execute_library_install(msg)


if __name__ == '__main__':
    unittest.main()
