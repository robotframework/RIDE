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
import random

from robotide.editor.gridbase import GridEditor

# wx needs to imported last so that robotide can select correct wx version.
import os
import pytest

from robotide.lib.robot.libraries.String import String

from robotide.controller.cellinfo import CellInfo, ContentType, CellType, CellContent, CellPosition
from robotide.editor.gridcolorizer import Colorizer

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
from robotide.namespace.suggesters import SuggestionSource
from robotide.editor.contentassist import (Suggestions, ContentAssistPopup, ContentAssistTextEditor,
                                           ContentAssistTextCtrl, ExpandingContentAssistTextCtrl,
                                           ContentAssistFileButton)

import os

# DISPLAY = os.getenv('DISPLAY')
# if not DISPLAY:
#     pytest.skip("Skipped because of missing DISPLAY", allow_module_level=True)  # Avoid failing unit tests in system without X11
import wx
import sys
from wx import Size
from robotide.robotapi import Variable
from robotide.controller import data_controller
from robotide.controller.robotdata import new_test_case_file
from robotide.controller.settingcontrollers import VariableController
from robotide.controller.tablecontrollers import VariableTableController
from robotide.editor import EditorPlugin, EditorCreator
from robotide.editor.kweditor import KeywordEditor
from robotide.editor.editors import TestCaseFileEditor, WelcomePage
from robotide.editor.popupwindow import HtmlPopupWindow
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

DATA = [['kw1', '', ''],
        ['kw2', 'arg1', ''],
        ['kw3', 'arg1', 'arg2']]

# frame.Show()
nb_style = aui.AUI_NB_DEFAULT_STYLE | aui.AUI_NB_WINDOWLIST_BUTTON | aui.AUI_NB_TAB_EXTERNAL_MOVE \
           | aui.AUI_NB_SUB_NOTEBOOK | aui.AUI_NB_SMART_TABS

myapp = wx.App(None)

class _FakeScrolledPanel(wx.lib.scrolledpanel.ScrolledPanel):

    def __init__(self, parent):
        wx.lib.scrolledpanel.ScrolledPanel.__init__(self, parent)

    def SetupScrolling(self):
        pass

    def GetScrollPixelsPerUnit(self):
        return  (20, 20)

    def GetViewStart(self):
        return (10, 10)


class MainFrame(wx.Frame, _FakeScrolledPanel):
    notebook = None

    def __init__(self):
        frame = wx.Frame.__init__(self, parent=None, title='Grid Editor Test App', size=Size(600, 400))
        _FakeScrolledPanel.__init__(self, frame)
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

    def _datafile_controller(self):
        return data_controller(new_test_case_file(datafilereader.TESTCASEFILE_WITH_EVERYTHING), None)

    def OnExit(self):  # Overrides wx method
        if hasattr(self, 'file_settings'):
            os.remove(self.file_settings)
        self.ExitMainLoop()


def EditorWithData():
    myapp = MyApp()
    grid = GridEditor(myapp.frame, 5, 5)
    for ridx, rdata in enumerate(DATA):
        for cidx, cdata in enumerate(rdata):
            grid.write_cell(ridx, cidx, cdata, update_history=False)
    return grid


class MockGrid(object):
    noop = lambda *args: None
    SetCellTextColour = SetCellBackgroundColour = SetCellFont = noop
    settings = {
        'font size': 10,
        'font face': '',
        'fixed font': False,
        'col size': 150,
        'max col size': 450,
        'auto size cols': False,
        'text user keyword': 'blue',
        'text library keyword': '#0080C0',
        'text variable': 'forest green',
        'text unknown variable': 'purple',
        'text commented': 'firebrick',
        'text string': 'black',
        'text empty': 'black',
        'background assign': '#FFFFFF',
        'background keyword': '#FFFFFF',
        'background mandatory': '#FFFFFF',
        'background optional': '#F5F5F5',
        'background must be empty': '#C0C0C0',
        'background unknown': '#FFFFFF',
        'background error': '#FF9385',
        'background highlight': '#FFFF77',
        'word wrap': True,
        'enable auto suggestions': False
    }

    def GetCellFont(self, x, y):
        return Font()


class Font(object):
    SetWeight = lambda s, x: True


class ControllerWithCellInfo(object):
    content_types = [getattr(ContentType, i) for i in
                     dir(ContentType) if not i.startswith('__') ]
    cell_types = [getattr(CellType, i) for i in
                  dir(CellType) if not i.startswith('__') ]

    def __init__(self):
        self._string = String()

    def get_cell_info(self, row, column):
        return CellInfo(CellContent(self._get(self.content_types), self._get_data(), None),
                        CellPosition(self._get(self.cell_types), None))

    def _get(self, items):
        return items[random.randint(0, len(items)-1)]

    def _get_data(self):
        if random.randint(0, 5) == 0:
            return "data with some ${variable} in there"
        return self._string.generate_random_string(50)


# @pytest.mark.skip('It is getting unexpected data')
class TestPerformance(unittest.TestCase):
    _data = ['Keyword', 'Some longer data in cell', '${variable}',
             '#asdjaskdkjasdkjaskdjkasjd', 'asdasd,asdasd,as asd jasdj asjd asjdj asd']

    def setUp(self):
        self._editor = EditorWithData()

    def test_colorizing_performance(self):
        colorizer = Colorizer(MockGrid(), ControllerWithCellInfo())
        for _ in range(0, 500):
            rdata = self._data[random.randint(0, 4)]
            self._editor.SetCellValue(1, 1, rdata)
            cdata = self._editor.GetCellValue(1, 1)
            colorizer._colorize_cell(1,1, cdata)


class TestColorIdentification(unittest.TestCase):
    _data = ['xyz', 'FOR', 'try', 'for', 'LOG']
    _type = [CellInfo(CellContent(ContentType.STRING, _data[0]), CellPosition(CellType.UNKNOWN, None)),
             CellInfo(CellContent(ContentType.LIBRARY_KEYWORD, _data[1]), CellPosition(CellType.ASSIGN, '${i}')),
             CellInfo(CellContent(ContentType.STRING, _data[2]), CellPosition(CellType.UNKNOWN, None)),
             CellInfo(CellContent(ContentType.STRING, _data[3]), CellPosition(CellType.UNKNOWN, None)),
             CellInfo(CellContent(ContentType.LIBRARY_KEYWORD, _data[4]), CellPosition(CellType.MANDATORY, 'Message'))
             ]

    def test_unknown_string(self):
        grid = MockGrid()
        colorizer = Colorizer(grid, ControllerWithCellInfo())
        txt_color = colorizer._get_text_color(self._type[0])
        # print(f"DEBUG: Text color={txt_color.title().upper()}")
        bk_color = colorizer._get_background_color(self._type[0], self._data[0])
        # print(f"DEBUG: Background color={bk_color.title().upper()}")
        assert txt_color.title().upper() == grid.settings['text string'].upper()
        assert bk_color.title().upper() == grid.settings['background highlight'].upper()  # I am cheating here ;)

    def test_valid_for(self):
        grid = MockGrid()
        colorizer = Colorizer(grid, ControllerWithCellInfo())
        txt_color = colorizer._get_text_color(self._type[1])
        # print(f"DEBUG: Text color={txt_color.title().upper()}")
        bk_color = colorizer._get_background_color(self._type[1], self._data[1])
        # print(f"DEBUG: Background color={bk_color.title().upper()}")
        assert txt_color.title().upper() == grid.settings['text library keyword'].upper()
        assert bk_color.title().upper() == grid.settings['background highlight'].upper()  # I am cheating here ;)

    def test_invalid_try(self):
        grid = MockGrid()
        colorizer = Colorizer(grid, ControllerWithCellInfo())
        txt_color = colorizer._get_text_color(self._type[2])
        # print(f"DEBUG: Text color={txt_color.title().upper()}")
        bk_color = colorizer._get_background_color(self._type[2], self._data[2])
        # print(f"DEBUG: Background color={bk_color.title().upper()}")
        assert txt_color.title().upper() == grid.settings['text string'].upper()
        assert bk_color.title().upper() == grid.settings['background highlight'].upper()  # I am cheating here ;)

    def test_invalid_for(self):
        grid = MockGrid()
        colorizer = Colorizer(grid, ControllerWithCellInfo())
        txt_color = colorizer._get_text_color(self._type[3])
        # print(f"DEBUG: Text color={txt_color.title().upper()}")
        bk_color = colorizer._get_background_color(self._type[3], self._data[3])
        # print(f"DEBUG: Background color={bk_color.title().upper()}")
        assert txt_color.title().upper() == grid.settings['text string'].upper()
        assert bk_color.title().upper() == grid.settings['background highlight'].upper()  # I am cheating here ;)

    def test_valid_log(self):
        grid = MockGrid()
        colorizer = Colorizer(grid, ControllerWithCellInfo())
        txt_color = colorizer._get_text_color(self._type[4])
        # print(f"DEBUG: Text color={txt_color.title().upper()}")
        bk_color = colorizer._get_background_color(self._type[4], self._data[4])
        # print(f"DEBUG: Background color={bk_color.title().upper()}")
        assert txt_color.title().upper() == grid.settings['text library keyword'].upper()
        assert bk_color.title().upper() == grid.settings['background highlight'].upper()  # I am cheating here ;)


if __name__ == '__main__':
    unittest.main()
