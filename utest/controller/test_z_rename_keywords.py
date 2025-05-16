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

import os
import sys
import unittest
from robotide.controller.ctrlcommands import (Undo, FindOccurrences, FindVariableOccurrences, NullObserver,
                                              RenameKeywordOccurrences, ChangeCellValue)
from robotide.controller.macrocontrollers import KeywordNameController

from .base_command_test import TestCaseCommandTest
from utest.resources import datafilereader

# Workaround for relative import in non-module
# see https://stackoverflow.com/questions/16981921/relative-imports-in-python-3
PACKAGE_PARENT = '..'
SCRIPT_DIR = os.path.dirname(os.path.realpath(os.path.join(os.getcwd(),
                                              os.path.expanduser(__file__))))
sys.path.insert(0, os.path.normpath(os.path.join(SCRIPT_DIR, PACKAGE_PARENT)))

SUITESETUPKW = 'Suite Setup Keyword'
GIVENAKW = 'Given a Keyword'
GIVENANEWKW = 'Given a new Keyword'
AKW = 'a Keyword'
WHENAKW = 'When a Keyword'

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
from robotide.editor.kweditor import KeywordEditor
from robotide.editor.gridbase import GridEditor
from robotide.namespace.namespace import Namespace

import os
import pytest
# DISPLAY = os.getenv('DISPLAY')
# if not DISPLAY: # Avoid failing unit tests in system without X11
#     pytest.skip("Skipped because of missing DISPLAY", allow_module_level=True)
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
"""
try:
    from fakeplugin import FakePlugin
except ImportError:  # Python 3
    from .fakeplugin import FakePlugin
"""
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

DATA = [['kw1', '', ''],
        ['kw2', 'arg1', ''],
        ['kw3', 'arg1', 'arg2']]

# frame.Show()
nb_style = aui.AUI_NB_DEFAULT_STYLE | aui.AUI_NB_WINDOWLIST_BUTTON | aui.AUI_NB_TAB_EXTERNAL_MOVE \
           | aui.AUI_NB_SUB_NOTEBOOK | aui.AUI_NB_SMART_TABS


class _FakeScrolledPanel(wx.lib.scrolledpanel.ScrolledPanel):

    def __init__(self, parent):
        wx.lib.scrolledpanel.ScrolledPanel.__init__(self, None)

    def SetupScrolling(self):
        pass


class MainFrame(wx.Frame, _FakeScrolledPanel):
    notebook = None

    def __init__(self):
        wx.Frame.__init__(self, parent=None, title='Grid Editor Test App')
        _FakeScrolledPanel.__init__(self, None)
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
        self.SetExitOnFrameDelete(True)

    def OnInit(self):  # Overrides wx method
        self.frame = MainFrame()
        self.SetTopWindow(self.frame)
        self.settings = FakeSettings()
        # _, self.file_settings = tempfile.mkstemp('.cfg', text=True)
        self.global_settings = RideSettings(self.settings.fake_cfg)  #self.file_settings)
        self.global_settings.add_section("Grid")
        self.settings.global_settings = self.global_settings
        self.settings.add_section("Grid")
        self.frame = MainFrame()
        self.SetTopWindow(self.frame)
        self.settings = FakeSettings()
        # _, self.file_settings = tempfile.mkstemp('.cfg', text=True)
        self.global_settings = RideSettings(self.settings.fake_cfg)  #self.file_settings)
        self.global_settings.add_section("Grid")
        self.settings.global_settings = self.global_settings
        self.settings.add_section("Grid")
        self.settings['Grid'].set('background unknown', '#E8B636')
        self.settings['Grid'].set('font size', 10)
        self.settings['Grid'].set('font face', '')
        self.settings['Grid'].set('zoom factor', 0)
        self.settings['Grid'].set('fixed font', False)
        self.settings['Grid'].set('col size', 150)
        self.settings['Grid'].set('max col size', 450)
        self.settings['Grid'].set('auto size cols', False)
        self.settings['Grid'].set('text user keyword', 'blue')
        self.settings['Grid'].set('text library keyword', '#0080C0')
        self.settings['Grid'].set('text variable', 'forest green')
        self.settings['Grid'].set('text unknown variable', 'purple')
        self.settings['Grid'].set('text commented', 'firebrick')
        self.settings['Grid'].set('text string', 'black')
        self.settings['Grid'].set('text empty', 'black')
        self.settings['Grid'].set('background assign', '#CADEF7')
        self.settings['Grid'].set('background keyword', '#CADEF7')
        self.settings['Grid'].set('background mandatory', '#D3D3D3')
        self.settings['Grid'].set('background optional', '#F9D7BA')
        self.settings['Grid'].set('background must be empty', '#C0C0C0')
        self.settings['Grid'].set('background error', '#FF9385')
        self.settings['Grid'].set('background highlight', '#FFFF77')
        self.settings['Grid'].set('word wrap', True)
        self.settings['Grid'].set('enable auto suggestions', True)
        self.settings['Grid'].set('filter newlines', False)
        self.highlight = lambda x, expand: x if expand else x
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
        self.plugin = EditorPlugin(self)
        self.plugin.title = 'Editor'
        # mb.register("File|Open")
        mb.take_menu_bar_into_use()
        self._mgr.Update()
        return True

    """
    def _datafile_controller(self):
        return data_controller(new_test_case_file(datafilereader.TESTCASEFILE_WITH_EVERYTHING), None)
    """

    def OnExit(self):  # Overrides wx method
        if hasattr(self, 'file_settings'):
            os.remove(self.file_settings)
        # self.ExitMainLoop()
        # self.Destroy()


def _first_occurrence(test_ctrl, kw_name):
    occurrences = test_ctrl.execute(FindOccurrences(kw_name))
    if not occurrences:
        raise AssertionError('No occurrences found for "%s"' % kw_name)
    return next(occurrences)
    # see https://stackoverflow.com/questions/21622193/
    # python-3-2-coroutine-attributeerror-generator-object-has-no-attribute-next


class TestRenameResourcePrefixedKeywords(unittest.TestCase):

    def setUp(self):
        self.app = MyApp()
        self.settings = self.app.settings
        self.frame = self.app.frame
        self.frame.tree = Tree(self.frame, ActionRegisterer(AuiManager(self.frame),
                                                            MenuBar(self.frame), ToolBar(self.frame),
                                                            ShortcutRegistry(self.frame)), self.settings)
        self.app.project = Project(self.app.namespace, self.app.settings)
        self._registered_editors = {}
        self.creator = EditorCreator(self._register)
        self.creator.register_editors()

        # self.plugin = self._datafile_plugin(self.app)

        """
        texteditor.SourceEditor(self.app.notebook, self.plugin.title,
                                                                texteditor.DataValidationHandler(self.plugin))
        """
        self.frame.notebook = self.app.notebook
        self.plugin = EditorPlugin(self.app)
        self.plugin.title = 'Editor'
        # self._grid = KeywordEditor(self.plugin, self.app.project.controller, self.frame.tree)
        #self.plugin._editor_component = kweditor.ContentAssistCellEditor(self.app.plugin, self.app.project.controller)
        # self._test = self._datafile_controller()  # testcase_controller()
        self._panel = wx.Panel(self.app.frame)
        sizer = wx.BoxSizer()
        self._grid = GridEditor(self.app, 20, 10)
        self._grid.SetSizer(sizer=sizer)
        # self.plugin._editor_component = kweditor.ContentAssistCellEditor(self._grid, self.app.project.controller)
        # self.editor = TestCaseEditor(self.app, self._grid, self._test, self.app.tree)
        # self.plugin._editor_component = KeywordEditor(self.plugin, self.editor, self.app.tree)

        # self.editor = self._datafile_editor()
        # self.editor = self.plugin.get_editor(TestCase)
        # Moved to test
        # self.plugin.enable()
        # self.project_ctrl = self.app.project.load_datafile(datafilereader.RESOURCE_PREFIXED_KEYWORDS_PATH,
        #                                                    MessageRecordingLoadObserver())
        self.app.project.load_datafile(datafilereader.RESOURCE_PREFIXED_KEYWORDS_PATH, MessageRecordingLoadObserver())
        testcase = TestDataDirectory(source=datafilereader.RESOURCE_PREFIXED_KEYWORDS_PATH, language=['English'])
        self.project_ctrl = TestDataDirectoryController(testcase, self.app.project)
        # self.app.tree.set_editor(self.plugin._editor_component)
        # print(f"DEBUG: setUp() dir self.project_ctrl ={dir(self.project_ctrl)}"
        #       f"\nself.app.project={dir(self.app.project)} ")

        self._get_controllers()

        # self.ctrl = self.ts1
        # self.suites = self.ctrl.suites
        self.app.tree.populate(self.app.project)

        for ridx, rdata in enumerate(DATA):
            for cidx, cdata in enumerate(rdata):
                self._grid.write_cell(ridx, cidx, cdata, update_history=False)

        self._editor = self._grid
        self.app.frame.SetStatusText("File:" + self.app.project.data.source)
        # Uncomment next line (and MainLoop in tests) if you want to see the app
        self.frame.Show()

    def _get_controllers(self):
        self.ts1 = datafilereader.get_ctrl_by_name('Suite01', self.app.project.datafiles)
        self.ts3 = datafilereader.get_ctrl_by_name('Suite02', self.app.project.datafiles)
        self.res00 = datafilereader.get_ctrl_by_name('External Res', self.app.project.datafiles)  # OK
        self.res01 = datafilereader.get_ctrl_by_name('Res01', self.app.project.datafiles)
        self.res02 = datafilereader.get_ctrl_by_name('Res02', self.app.project.datafiles)

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

    """
    def _variable_plugin(self):
        return FakePlugin(self._registered_editors,
                          VariableController(VariableTableController(
                              self._datafile_controller(), None),
                              Variable(None, '','')))

    def _no_item_selected_plugin(self):
        return FakePlugin(self._registered_editors, None)
    """

    def _datafile_controller(self):
        return data_controller(new_test_case_file(datafilereader.RESOURCE_PREFIXED_KEYWORDS_PATH), None)

    def tearDown(self):
        self.plugin.unsubscribe_all()
        PUBLISHER.unsubscribe_all()
        self.app.project.close()
        # wx.CallAfter(self.app.ExitMainLoop)
        # self.app.MainLoop()  # With this here, there is no Segmentation fault
        # wx.CallAfter(wx.Exit)
        self.app.Destroy()
        self.app = None
        if os.path.exists(DATADIR):
            shutil.rmtree(DATADIR, ignore_errors=True)

    def test_rename_suite_setup_kw(self):
        """
        ts_list = []
        if isinstance(self.ts1, list):
            for x in self.ts1:
                ts_list.extend([s for s in x.tests.items])
        else:
            ts_list.append(self.ts1.tests.items)  # .get_keyword_names()  # [0].get_keyword_names() (self.suites)
        res_list = []
        if isinstance(self.res00, list):
            for x in self.res00:
                print(f"DEBUG: TestRenameResourcePrefixedKeywords test_rename_suite_setup_kw"
                      f" type(x)={type(x)} res_list={self.res00}\n")
                for y in x.keywords:
                    res_list.append(y)
        else:
            for x in self.res00.keywords:
                print(f"DEBUG: TestRenameResourcePrefixedKeywords test_rename_suite_setup_kw"
                      f" NOT LIST BRANCH type(x)={type(x)} res_list={x.steps}\n")
                res_list.append(x)
        if isinstance(self.res01, list):
            for x in self.res01:
                print(f"DEBUG: TestRenameResourcePrefixedKeywords test_rename_suite_setup_kw"
                      f" type(x)={type(x)} res_list={self.res01}\n")
                for y in x.keywords:
                    res_list.append(y)
        else:
            for x in self.res01.keywords:
                print(f"DEBUG: TestRenameResourcePrefixedKeywords test_rename_suite_setup_kw"
                      f" NOT LIST BRANCH type(x)={type(x)} res_list={x.steps}\n")
                res_list.append(x)
        if isinstance(self.res02, list):
            for x in self.res02:
                print(f"DEBUG: TestRenameResourcePrefixedKeywords test_rename_suite_setup_kw"
                      f" type(x)={type(x)} res_list={self.res02}\n")
                for y in x.keywords:
                    res_list.append(y)
        else:
            for x in self.res02.keywords:
                print(f"DEBUG: TestRenameResourcePrefixedKeywords test_rename_suite_setup_kw"
                      f" NOT LIST BRANCH type(x)={type(x)} res_list={x.steps}\n")
                res_list.append(x)
        if isinstance(self.ts3, list):
            for x in self.ts3:
                ts_list.extend([s for s in x.tests.items])
        else:
            ts_list.append(self.ts3.tests.items)
        """
        # settings = self.suites[0].setting_table
        # suite_setup = settings.suite_setup.as_list()
        # print(f"DEBUG: TestRenameResourcePrefixedKeywords test_rename_suite_setup_kw"
        #       f" source= {self.ctrl.source}  type ctrl={type(self.ctrl)} suites={self.suites}\n")
        """
        print(f"DEBUG: TestRenameResourcePrefixedKeywords test_rename_suite_setup_kw"
              f" type(kw_list)={type(kw_list)} kw_list= {kw_list}\n")
        print(f"DEBUG: TestRenameResourcePrefixedKeywords test_rename_suite_setup_kw"
              f" type(res_list)={type(res_list)} res_list={res_list}\n")
        print(f"DEBUG: TestRenameResourcePrefixedKeywords test_rename_suite_setup_kw"
              f" type(ts3_list)={type(ts3_list)} ts3_list={ts3_list}\n")
        """
        """
        assert ts_list is not None
        assert res_list is not None
        steps = []
        for k in ts_list + res_list:
            if hasattr(k, 'steps'):
                for s in k.steps:
                    steps.extend(s.as_list())
            # print(f"DEBUG: TestRenameResourcePrefixedKeywords test_rename_suite_setup_kw k is {type(k)}")
        print(f"DEBUG: TestRenameResourcePrefixedKeywords test_rename_suite_setup_kw"
              f" all steps ={steps[:]}\n")
        """
        """
        for test in self.ts1:
            print(f"DEBUG: TestRenameResourcePrefixedKeywords test_rename_suite_setup_kw ts1 ={test.name} "
                  f"source ={test.source}")
            for nm in test.tests:
                print(f"name={nm.name} ")
        for kw in res_list:
            print(f"DEBUG: TestRenameResourcePrefixedKeywords test_rename_suite_setup_kw resource kw={kw}")
        """
        occ_list = set()
        print(f"DEBUG: TestRenameResourcePrefixedKeywords test_rename_suite_setup_kw controller={self.project_ctrl.datafiles}")
        for obj in self.project_ctrl.datafiles:
            print(f"DEBUG: TestRenameResourcePrefixedKeywords test_rename_suite_setup_kw retrieve_test_controllers"
                  f" obj={obj.display_name} source={obj.source} type={type(obj)}")
            occurrences = obj.execute(FindOccurrences("keyword1", prefix="res02"))
            # print(occurrences)
            occ_list.add(occurrences)

        # print(f"Before Rename occ_list={occ_list}\n"
        #       f" len={len(occ_list)}")
        for occ in occ_list:
            for oo in occ:
                print(f"DEBUG: TestRenameResourcePrefixedKeywords test_rename_suite_setup_kw oo_item:{oo.item} "
                      f" oo_value:{oo._value} ")  #
                if not isinstance(oo.item, KeywordNameController):
                    print(f"oo_source:{oo.source} ")
           # print(f"DEBUG: TestRenameResourcePrefixedKeywords test_rename_suite_setup_kw FindOccurrences occ={occ}")
           #      f" {occ.item}")
        return
        observer = NullObserver()
        myobject = RenameKeywordOccurrences("keyword1", "kywd1", observer)
        print(f"Result from Rename myobject={myobject}")  # self.project_ctrl.datafiles: self.app.project.datafiles
        for obj in self.app.project.datafiles:
            myobject.execute(obj)
        print(f"DEBUG: TestRenameResourcePrefixedKeywords AFTER RENAME\n"
              f"is_dirty? {self.app.project.is_dirty()}")

        rocc_list = []
        for obj in self.project_ctrl.datafiles:
            occurrences = obj.execute(FindOccurrences("keyword1", prefix="res02"))
            rocc_list.extend(occurrences)
        print(f"After Result from Rename rocc_list={rocc_list} len={len(rocc_list)}")
        for occ in rocc_list:
            print(f"DEBUG: TestRenameResourcePrefixedKeywords test_rename_suite_setup_kw FindOccurrences occ={occ}")

        """
        occurrences = self.project_ctrl.execute(FindOccurrences("keyword2"))
        occ = _first_occurrence(self.project_ctrl, 'keyword2')
        print(f"DEBUG: TestRenameResourcePrefixedKeywords test_rename_suite_setup_kw Called _first_occurrence_first_occurrence"
        3      f" occ={occ.item}")
        # assert occ.item.parent.source == 'testdata_resource.robot'
        print(f"DEBUG: TestRenameResourcePrefixedKeywords test_rename_suite_setup_kw Called FindOccurrences occurrences={occurrences}")
        for occ in occurrences:
            print(f"DEBUG: TestRenameResourcePrefixedKeywords test_rename_suite_setup_kw FindOccurrences occ={occ}"
                  f" {occ.source}")

        myobject.execute(self.ts1[0])
        myobject.execute(self.ts1[1])
        myobject.execute(self.ts3)
        myobject.execute(self.res00)
        myobject.execute(self.res01)
        myobject.execute(self.res02)
        """

        return
        # myobject.execute(self.project_ctrl.setting_table)
        # After Rename
        self._get_controllers()

        print(f"Result from Rename myobject={myobject}")
        ts_list = []
        if isinstance(self.ts1, list):
            for x in self.ts1:
                ts_list.extend([s for s in x.tests.items])
        else:
            ts_list.append(self.ts1.tests.items)  # .get_keyword_names()  # [0].get_keyword_names() (self.suites)
        res_list = []
        if isinstance(self.res00, list):
            for x in self.res00:
                print(f"DEBUG: TestRenameResourcePrefixedKeywords test_rename_suite_setup_kw"
                      f" type(x)={type(x)} res_list={self.res00}\n")
                for y in x.keywords:
                    res_list.append(y)
        else:
            for x in self.res00.keywords:
                print(f"DEBUG: TestRenameResourcePrefixedKeywords test_rename_suite_setup_kw"
                      f" NOT LIST BRANCH type(x)={type(x)} res_list={x.steps}\n")
                res_list.append(x)
        if isinstance(self.res01, list):
            for x in self.res01:
                print(f"DEBUG: TestRenameResourcePrefixedKeywords test_rename_suite_setup_kw"
                      f" type(x)={type(x)} res_list={self.res01}\n")
                for y in x.keywords:
                    res_list.append(y)
        else:
            for x in self.res01.keywords:
                print(f"DEBUG: TestRenameResourcePrefixedKeywords test_rename_suite_setup_kw"
                      f" NOT LIST BRANCH type(x)={type(x)} res_list={x.steps}\n")
                res_list.append(x)
        if isinstance(self.res02, list):
            for x in self.res02:
                print(f"DEBUG: TestRenameResourcePrefixedKeywords test_rename_suite_setup_kw"
                      f" type(x)={type(x)} res_list={self.res02}\n")
                for y in x.keywords:
                    res_list.append(y)
        else:
            for x in self.res02.keywords:
                print(f"DEBUG: TestRenameResourcePrefixedKeywords test_rename_suite_setup_kw"
                      f" NOT LIST BRANCH type(x)={type(x)} res_list={x.steps}\n")
                res_list.append(x)
        if isinstance(self.ts3, list):
            for x in self.ts3:
                ts_list.extend([s for s in x.tests.items])
        else:
            ts_list.append(self.ts3.tests.items)
        ren_steps = []
        for k in ts_list + res_list:
            if hasattr(k, 'steps'):
                for s in k.steps:
                    ren_steps.extend(s.as_list())
            # print(f"DEBUG: TestRenameResourcePrefixedKeywords test_rename_suite_setup_kw k is {type(k)}")
        print(f"DEBUG: TestRenameResourcePrefixedKeywords test_rename_suite_setup_kw"
              f" all Renamed steps ={ren_steps[:]}\n")
        assert steps[:] != ren_steps[:]
        """    
        for test in self.ts2:
            print(f"DEBUG: TestRenameResourcePrefixedKeywords test_rename_suite_setup_kw ts2 ={test.name} "
                  f"source ={test.source}")
        print(f"DEBUG: TestRenameResourcePrefixedKeywords test_rename_suite_setup_kw ts3 ={self.ts3.name}"
              f" source ={self.ts3.source}")
        """
        # wx.CallLater(5000, self.app.frame.Destroy)
        # self.app.MainLoop()
        # assert suite_setup is not None
        """
        assert kw_list == ['First KW', 'Second KW', 'Test Setup Keyword', 'Test Teardown Keyword',
                           'Keyword Teardown Keyword', SUITESETUPKW, 'Test Teardown in Setting']
        assert suite_setup == ['Suite Setup', 'Run Keywords', SUITESETUPKW, 'AND', 'First KW']
        observer = NullObserver()
        myobject = RenameKeywordOccurrences("First KW", "One Keyword", observer)
        myobject.execute(self.suites[0])
        kw_list = self.suites[0].get_keyword_names()
        settings = self.suites[0].setting_table
        suite_setup = settings.suite_setup.as_list()
        # print(f"DEBUG: kw.list are: {kw_list} \n suite_setup={suite_setup}")
        assert kw_list == ['One Keyword', 'Second KW', 'Test Setup Keyword', 'Test Teardown Keyword',
                           'Keyword Teardown Keyword', SUITESETUPKW, 'Test Teardown in Setting']
        assert suite_setup == ['Suite Setup', 'Run Keywords', SUITESETUPKW, 'AND', 'One Keyword']
        """


if __name__ == "__main__":
    unittest.main()
