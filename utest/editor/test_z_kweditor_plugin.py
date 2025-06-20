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
import os
import pytest
import shutil
import sys
import unittest
import wx
import wx.lib.agw.aui as aui

from wx import Size
from multiprocessing import shared_memory
from wx.lib.agw.buttonpanel import BoxSizer
from utest.resources import datafilereader, MessageRecordingLoadObserver
from robotide.ui.mainframe import ActionRegisterer, ToolBar
from robotide.ui.actiontriggers import MenuBar, ShortcutRegistry
from robotide.application import Project
from robotide.application import RIDE
from robotide.ui.treeplugin import Tree
from robotide.ui.notebook import NoteBook
from robotide.namespace.suggesters import SuggestionSource
from robotide.editor.contentassist import (ContentAssistPopup, ContentAssistTextEditor,
                                           ContentAssistTextCtrl, ExpandingContentAssistTextCtrl,
                                           ContentAssistFileButton)
# DISPLAY = os.getenv('DISPLAY')
# if not DISPLAY: # Avoid failing unit tests in system without X11
#     pytest.skip("Skipped because of missing DISPLAY", allow_module_level=True)
from robotide.robotapi import Variable
from robotide.controller import data_controller
from robotide.controller.robotdata import new_test_case_file
from robotide.controller.settingcontrollers import VariableController
from robotide.controller.tablecontrollers import VariableTableController
from robotide.editor import EditorPlugin, EditorCreator
from robotide.editor.editors import TestCaseFileEditor
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
MYTESTOVERRIDE = 'My Overriding Test Teardown'

LANGUAGES = [('Bulgarian', 'bg'), ('Bosnian', 'bs'),
             ('Czech', 'cs'), ('German', 'de'),
             ('English', 'en'), ('Spanish', 'es'),
             ('Finnish', 'fi'), ('French', 'fr'),
             ('Hindi', 'hi'), ('Italian', 'it'),
             ('Japanese', 'ja'), # Since RF 7.0.1
             ('Korean', 'ko'),  # Since RF 7.1
             ('Dutch', 'nl'), ('Polish', 'pl'),
             ('Portuguese', 'pt'),
             ('Brazilian Portuguese', 'pt-BR'),
             ('Romanian', 'ro'), ('Russian', 'ru'),
             ('Swedish', 'sv'), ('Thai', 'th'),
             ('Turkish', 'tr'), ('Ukrainian', 'uk'),
             ('Vietnamese', 'vi'),
             ('Chinese Simplified', 'zh-CN'),
             ('Chinese Traditional', 'zh-TW')]

"""
app = mock(RIDE(path=None, updatecheck=False))
frame = wx.Frame(parent=None, title='Test Frame')
app.frame = frame
app.namespace = mock(Namespace)
app.settings = FakeSettings()
app.register_editor()
"""
generic_app = wx.App()

DATA = [['kw1', '', ''],
        ['kw2', 'arg1', ''],
        ['kw3', 'arg1', 'arg2']]

# frame.Show()
nb_style = aui.AUI_NB_DEFAULT_STYLE | aui.AUI_NB_WINDOWLIST_BUTTON | aui.AUI_NB_TAB_EXTERNAL_MOVE \
           | aui.AUI_NB_SUB_NOTEBOOK | aui.AUI_NB_SMART_TABS


class MainFrame(wx.Frame):
    book = None

    def __init__(self):
        wx.Frame.__init__(self, parent=None, title='Grid Editor Test App', size=Size(600, 400))
        self.CreateStatusBar()


class MyApp(RIDE):
    frame = None
    namespace = None
    project = None
    settings = None
    notebook = None
    panel = None
    tree = None
    model = None

    def __init__(self, path=None, updatecheck=True, settingspath=None):
        # redirect=False, filename=None, usebestvisual=False, clearsigint=True):
        self.actions = None
        self.toolbar = None
        self._mgr = None
        RIDE.__init__(self, path, updatecheck, settingspath)


    def OnInit(self):  # Overrides wx method
        self.frame = MainFrame()
        self.SetTopWindow(self.frame)
        self.settings = FakeSettings()
        self.settings = RideSettings(self.settings.fake_cfg)  # self.file_settings)
        # self.global_settings.add_section("Grid")
        # self.settings.global_settings = self.global_settings
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
        self.namespace = Namespace(self.settings)
        self.notebook = NoteBook(self.frame, self, nb_style)
        self.panel = wx.lib.scrolledpanel.ScrolledPanel(self.frame, -1)
        self.frame.notebook = self.notebook
        self._mgr = aui.AuiManager()

        # tell AuiManager to manage this frame
        self._mgr.SetManagedWindow(self.frame)
        self.notebook.SetBackgroundColour(wx.Colour(255, 255, 255))
        self.notebook.SetForegroundColour(wx.Colour(0, 0, 0))
        self._mgr.AddPane(self.notebook,
                          aui.AuiPaneInfo().Name("notebook_editors").
                          CenterPane().PaneBorder(False))
        mb = MenuBar(self.frame)
        self.toolbar = ToolBar(self.frame)
        self.toolbar.SetMinSize(wx.Size(100, 60))
        self.toolbar.SetBackgroundColour(wx.Colour(255, 255, 255))
        self.toolbar.SetForegroundColour(wx.Colour(0, 0, 0))
        # self.SetToolBar(self.toolbar.GetToolBar())
        mb.m_frame.SetBackgroundColour(wx.Colour(255, 255, 255))
        mb.m_frame.SetForegroundColour(wx.Colour(0, 0, 0))
        self._mgr.AddPane(self.toolbar, aui.AuiPaneInfo().Name("maintoolbar").
                          ToolbarPane().Top())
        self.frame.actions = ActionRegisterer(self._mgr, mb, self.toolbar, ShortcutRegistry(self.frame))
        self.tree = Tree(self.frame, self.frame.actions, self.settings)
        self.tree.SetMinSize(wx.Size(275, 250))
        self.frame.SetMinSize(wx.Size(600, 400))
        self._mgr.AddPane(self.tree,
                          aui.AuiPaneInfo().Name("tree_content").Caption("Test Suites").CloseButton(False).
                          LeftDockable())
        # mb.register("File|Open")
        # self.highlight = lambda x, expand: x if expand else x
        # self.plugin = kweditor.KeywordEditor(self, self._datafile_controller(), self.tree)
        mb.take_menu_bar_into_use()
        self._mgr.Update()
        return True

    def _datafile_controller(self):
        return data_controller(new_test_case_file(datafilereader.SIMPLE_PROJECT), self.project)

    def OnExit(self):  # Overrides wx method
        if hasattr(self, 'file_settings'):
            os.remove(self.file_settings)
        self.ExitMainLoop()
        return 0


class KeywordEditorTest(unittest.TestCase):

    def setUp(self):
        self.app = MyApp()
        self.settings = self.app.settings
        try:
            self.shared_mem = shared_memory.ShareableList(['en'], name="language")
        except FileExistsError:  # Other instance created file
            self.shared_mem = shared_memory.ShareableList(name="language")
        self.frame = self.app.frame
        self.frame.actions = ActionRegisterer(aui.AuiManager(self.frame), MenuBar(self.frame), ToolBar(self.frame),
                                              ShortcutRegistry(self.frame))
        self.frame.tree = Tree(self.frame, self.frame.actions, self.settings)
        self.app.project = Project(self.app.namespace, self.app.settings)
        self.app.project.load_datafile(datafilereader.SIMPLE_PROJECT, MessageRecordingLoadObserver())
        self.app.model = self.app.project.data
        self.panel = self.app.panel
        self.namespace = self.app.project.namespace
        self.controllers = self.app.project.all_testcases()
        self.test_case = next(self.controllers)
        self.plugin = EditorPlugin(self.app)
        self.plugin.add_self_as_tree_aware_plugin()
        self.app.tree.populate(self.app.project)
        self.source = self.app.tree.controller
        sizer = BoxSizer()
        sizer.Add(self.app.panel)
        managed_window = self.app._mgr.GetManagedWindow()  # "notebook_editors"
        managed_window.SetSizer(sizer)
        self._grid = TestCaseEditor(self.plugin, managed_window, self.test_case, self.frame.tree)
        self.plugin.add_tab(self._grid, 'Editor')
        self.app.frame.SetStatusText("File:" + self.app.project.data.source)
        self._registered_editors = {}
        self.creator = EditorCreator(self._register)
        self.creator.register_editors()
        """
        for ridx, rdata in enumerate(DATA):
            for cidx, cdata in enumerate(rdata):
                self._grid.kweditor.write_cell(ridx, cidx, cdata, update_history=False)
        """
        # Uncomment next line (and MainLoop in tests) if you want to see the app
        self.frame.Show()
        self.SHOWING = True
        self.frame.Center()
        # wx.CallLater(1000, self.app.MainLoop)

    def _register(self, iclass, eclass):
        self._registered_editors[iclass] = eclass

    def _editor_for(self, plugin):
        return self.creator.editor_for(plugin, self.frame, self.app.tree)

    def _datafile_editor(self):
        return self.creator.editor_for(self.plugin, self.frame, self.app.tree)  # self._datafile_plugin(self.app)

    def _datafile_plugin(self, parent):
        # return FakePlugin(self._registered_editors, self._datafile_controller())
        print(f"DEBUG: _datafile_plugin parent={parent}")
        return TestCaseEditor(self.plugin, self._grid, self.test_case, self.app.tree)

    def _variable_plugin(self):
        return FakePlugin(self._registered_editors,
                          VariableController(VariableTableController(
                              self._datafile_controller(), None),
                              Variable(None, '','')))

    def _no_item_selected_plugin(self):
        return FakePlugin(self._registered_editors, None)

    def _datafile_controller(self):
        return data_controller(new_test_case_file(datafilereader.SIMPLE_PROJECT), self.app.project)

    def tearDown(self):
        self.shared_mem.shm.close()
        self.shared_mem.shm.unlink()
        self.app.ExitMainLoop()
        self.app.Destroy()
        self.app = None
        if os.path.exists(DATADIR):
            shutil.rmtree(DATADIR, ignore_errors=True)

    def setup_data(self):
        for ridx, rdata in enumerate(DATA):
            for cidx, cdata in enumerate(rdata):
                self._grid.kweditor.write_cell(ridx, cidx, cdata, update_history=False)

    """
    def test_enable(self):
        self.plugin.enable()

    def test_is_focused(self):
        focused = self.plugin.is_focused()
        assert focused is True
        # wx.CallLater(5000, self.app.ExitMainLoop)
        # self.app.MainLoop()
    """

    """
    def test_highlight_cell(self):
        highlight = self.plugin.highlight_cell('None')
        assert highlight is True

    def test_disable(self):
        self.plugin.disable()
    """

    def test_show(self):
        # self.setup_data()
        self.frame.Show()
        self.app.tree.select_controller_node(self.test_case)
        show = self.frame.Children
        print(f"DEBUG: test_show is children={[n.Name for n in show]}")
        tabs = self._grid.kweditor.GetParent().GetName()
        print(f"DEBUG: test_show Parent Name={tabs}")
        self._grid.kweditor.SetFocus()
        show = self._grid.kweditor.has_focus()
        assert show  # is not None
        # Uncomment next lines if you want to see the app
        wx.CallLater(5000, self.app.ExitMainLoop)
        self.app.MainLoop()

    def test_on_comment_cells(self):
        self.setup_data()
        self.frame.Show()
        # self.creator.editor_for(self.app.plugin, self._panel, self.frame.tree)
        self._grid.kweditor.SelectBlock(2, 2, 2, 2)
        sel = self._grid.kweditor.selection
        data = self._grid.kweditor.get_selected_content()
        print(f"DEBUG: Data Cell is {data} sel={sel}")
        self._grid.kweditor.on_comment_cells(None)  # THIS IS NOT WORKING
        data = self._grid.kweditor.get_selected_content()
        print(f"DEBUG: After Sharp Comment Data Cell is {data}")
        wx.CallLater(5000, self.app.ExitMainLoop)
        # self.app.MainLoop()


    """ Clipboard tests moved from test_grid.py to here """
    @pytest.mark.skip()
    def test_copy_one_cell(self):
        self.setup_data()
        self.frame.Show()
        print("")
        for row in range(3):
            text = f"{row}: "
            for col in range(3):
                cell = self._grid.kweditor.GetCellValue(row, col)
                text += f" {cell} |"
            print(f"{text}")
        self._copy_block_and_verify((0, 0, 0, 0), [['kw1']])
        # Uncomment next lines if you want to see the app
        # wx.CallLater(5000, self.app.ExitMainLoop)
        # self.app.MainLoop()

    @pytest.mark.skip()
    def test_copy_row(self):
        self._copy_block_and_verify((1, 0, 1, 1), [[val for val in DATA[1] if val]])
        # Uncomment next lines if you want to see the app
        # wx.CallLater(5000, self.app.ExitMainLoop)
        # self.app.MainLoop()

    @pytest.mark.skip()
    def test_copy_block(self):
        self.setup_data()
        self.frame.Show()
        self._copy_block_and_verify((0, 0, 2, 2), DATA)
        # Uncomment next lines if you want to see the app
        # wx.CallLater(5000, self.app.ExitMainLoop)
        # self.app.MainLoop()

    def _copy_block_and_verify(self, block, exp_content):
        self._grid.kweditor.SelectBlock(*block)
        self._grid.kweditor.copy()
        print(f"\nClipboard Content: {self._grid.kweditor._clipboard_handler._clipboard.get_contents()}")
        assert (self._grid.kweditor._clipboard_handler._clipboard.get_contents() == exp_content)
        self._verify_grid_content(DATA)

    def test_cut_one_cell(self):
        self.setup_data()
        self.frame.Show()
        self._cut_block_and_verify((0, 0, 0, 0), [['kw1']],
                                   [['', '', '']] + DATA[1:])
        # Uncomment next lines if you want to see the app
        # wx.CallLater(5000, self.app.ExitMainLoop)
        # self.app.MainLoop()

    def test_cut_row(self):
        self.setup_data()
        self.frame.Show()
        self._cut_block_and_verify((2, 0, 2, 2), [DATA[2]], DATA[:2])
        # Uncomment next lines if you want to see the app
        # wx.CallLater(5000, self.app.ExitMainLoop)
        # self.app.MainLoop()

    def test_cut_block(self):
        self.setup_data()
        self.frame.Show()
        self._cut_block_and_verify((0, 0, 2, 2), DATA, [])
        # Uncomment next lines if you want to see the app
        wx.CallLater(5000, self.app.ExitMainLoop)
        # self.app.MainLoop()

    def _cut_block_and_verify(self, block, exp_clipboard, exp_grid):
        self._cut_block(block)
        assert (self._grid.kweditor._clipboard_handler._clipboard.get_contents() ==
                exp_clipboard)
        self._verify_grid_content(exp_grid)

    def test_undo_with_cut(self):
        self.setup_data()
        self.frame.Show()
        self._cut_block((0, 0, 0, 0))
        self._grid.kweditor.undo()
        self._verify_grid_content(DATA)
        self._cut_block((0, 0, 2, 2))
        # We have problems here. We need undo for each cell removed
        self._grid.kweditor.undo()
        self._grid.kweditor.undo()
        self._grid.kweditor.undo()
        self._grid.kweditor.undo()
        self._grid.kweditor.undo()
        self._grid.kweditor.undo()
        self._verify_grid_content(DATA)
        # Uncomment next lines if you want to see the app
        # wx.CallLater(5000, self.app.ExitMainLoop)
        # self.app.MainLoop()

    def test_multiple_levels_of_undo(self):
        self.setup_data()
        self.frame.Show()
        self._cut_block((0, 0, 0, 0))
        self._cut_block((2, 0, 2, 2))
        # We have problems here. We need undo for each cell removed
        self._grid.kweditor.undo()
        self._grid.kweditor.undo()
        self._grid.kweditor.undo()
        self._verify_grid_content([['', '', '']] + DATA[1:])
        self._grid.kweditor.undo()
        self._verify_grid_content(DATA)
        # Uncomment next lines if you want to see the app
        # wx.CallLater(5000, self.app.ExitMainLoop)
        # self.app.MainLoop()

    def _cut_block(self, block):
        self._grid.kweditor.SelectBlock(*block)
        self._grid.kweditor.cut()

    def test_paste_one_cell(self):
        self.setup_data()
        self.frame.Show()
        self._copy_and_paste_block((1, 0, 1, 0), (3, 0, 3, 0), DATA + [['kw2']])
        # These tests are not independent
        self._copy_and_paste_block((1, 0, 1, 0), (0, 3, 0, 3),
                                   [DATA[0] + ['kw2']] + DATA[1:] + [['kw2']])
        # Uncomment next lines if you want to see the app
        # wx.CallLater(5000, self.app.ExitMainLoop)
        # self.app.MainLoop()

    def test_paste_row(self):
        self.setup_data()
        self.frame.Show()
        self._copy_and_paste_block((2, 0, 2, 2), (3, 1, 3, 1), DATA + [[''] + DATA[2]])
        # Uncomment next lines if you want to see the app
        # wx.CallLater(5000, self.app.ExitMainLoop)
        # self.app.MainLoop()

    def test_paste_block(self):
        self.setup_data()
        self.frame.Show()
        self._copy_and_paste_block((0, 0, 2, 2), (4, 0, 4, 0), DATA + [['']] + DATA)
        # Uncomment next lines if you want to see the app
        # wx.CallLater(5000, self.app.ExitMainLoop)
        # self.app.MainLoop()

    # @pytest.mark.skip()
    def test_paste_over(self):
        self.setup_data()
        self.frame.Show()
        self._copy_and_paste_block((1, 0, 1, 1), (0, 0, 0, 0), [DATA[1]] + DATA[1:])
        # Uncomment next lines if you want to see the app
        # wx.CallLater(5000, self.app.ExitMainLoop)
        # self.app.MainLoop()

    def _copy_and_paste_block(self, sourceblock, targetblock, exp_content):
        self._grid.kweditor.SelectBlock(*sourceblock)
        self._grid.kweditor.copy()
        self._grid.kweditor.SelectBlock(*targetblock)
        self._grid.kweditor.paste()
        self._verify_grid_content(exp_content)

    def _verify_grid_content(self, data):
        for row in range(self._grid.kweditor.NumberRows):
            for col in range(self._grid.kweditor.NumberCols):
                value = self._grid.kweditor.GetCellValue(row, col)
                try:
                    assert value == data[row][col], f"The contents of cell ({row},{col}) was not as expected"
                except IndexError:
                    assert value == ''

    def test_simple_undo(self):
        self.setup_data()
        self.frame.Show()
        self._grid.kweditor.SelectBlock(*(0, 0, 0, 0))
        self._grid.kweditor.cut()
        self._grid.kweditor.undo()
        self._verify_grid_content(DATA)
        # Uncomment next lines if you want to see the app
        # wx.CallLater(5000, self.app.ExitMainLoop)
        # self.app.MainLoop()

    # @pytest.mark.skip()
    def test_contentassist_dialog(self):
        suggestions = SuggestionSource(None, self.test_case)
        suggestions.update_from_local(['No Operation', 'Log Many', 'Log', '${CURDIR}'], 'en')
        dlg = ContentAssistPopup(self._grid.kweditor, suggestions)
        dlg.show(600, 400, 20)
        result = dlg.content_assist_for('Log Many')
        shown=dlg.is_shown()
        print(f"DEBUG: test_z_kweditor.py: content_assist_for result={result} shown={shown}")
        assert shown is True
        dlg._move_x_where_room(800)
        dlg._move_y_where_room(400, 20)
        # dlg.reset()
        value = dlg.content_assist_value('${CUR')
        dlg.select_and_scroll(wx.WXK_DOWN)
        dlg.dismiss()
        dlg.hide()
        # wx.CallLater(4000, dlg.hide)
        # Uncomment next lines if you want to see the app
        # wx.CallLater(5000, self.app.ExitMainLoop)
        # self.app.MainLoop()

    def test_htmlpopupwindow_dialog_simple(self):
        dlg = HtmlPopupWindow(self.frame, (400, 200), False, True)
        dlg.set_content("Example without title")
        dlg.show_at((1000, 200))
        shown=dlg.IsShown()
        print(f"DEBUG: test_z_kweditor.py: test_htmlpopupwindow_dialog_simple shown={shown}")
        assert shown is True
        # wx.CallLater(4000, dlg.hide)
        # Uncomment next lines if you want to see the app
        # wx.CallLater(5000, self.app.ExitMainLoop)
        # self.app.MainLoop()

    def test_htmlpopupwindow_dialog_title(self):
        dlg = HtmlPopupWindow(self.panel, (400, 200), True, True)
        dlg.set_content("Example with title", "This is the Title")
        dlg.show_at((1000, 100))
        shown=dlg.IsShown()
        assert shown is True
        pw_size = dlg.pw_size
        pw_pos = dlg.screen_position
        print(f"DEBUG: test_z_kweditor.py: test_htmlpopupwindow_dialog_title pw_size={pw_size} scree_pos={pw_pos}")
        event=wx.KeyEvent()
        dlg._detach(event)
        title = dlg._detached_title
        print(f"DEBUG: test_z_kweditor.py: test_htmlpopupwindow_dialog_title title={title}")
        # wx.CallLater(4000, dlg.hide)
        # Uncomment next lines if you want to see the app
        wx.CallLater(5000, self.app.ExitMainLoop)
        # self.app.MainLoop()

    def test_htmlpopupwindow_dialog_simple(self):
        dlg = HtmlPopupWindow(self.frame, (400, 200), False, True)
        dlg.set_content("Example without title")
        dlg.show_at((1000, 200))
        shown=dlg.IsShown()
        print(f"DEBUG: test_z_kweditor.py: test_htmlpopupwindow_dialog_simple shown={shown}")
        assert shown is True
        wx.CallLater(4000, dlg.hide)
        # Uncomment next lines if you want to see the app
        wx.CallLater(5000, self.app.ExitMainLoop)
        # self.app.MainLoop()

    def test_htmlpopupwindow_dialog_title(self):
        dlg = HtmlPopupWindow(self.panel, (400, 200), True, True)
        dlg.set_content("Example with title", "This is the Title")
        dlg.show_at((1000, 100))
        shown=dlg.IsShown()
        assert shown is True
        pw_size = dlg.pw_size
        pw_pos = dlg.screen_position
        print(f"DEBUG: test_z_kweditor.py: test_htmlpopupwindow_dialog_title pw_size={pw_size} scree_pos={pw_pos}")
        event=wx.KeyEvent()
        dlg._detach(event)
        title = dlg._detached_title
        print(f"DEBUG: test_z_kweditor.py: test_htmlpopupwindow_dialog_title title={title}")
        wx.CallLater(4000, dlg.hide)
        # Uncomment next lines if you want to see the app
        wx.CallLater(5000, self.app.ExitMainLoop)
        # self.app.MainLoop()

    def test_contentassist_text_editor(self):
        suggestions = SuggestionSource(None, self.app.project.controller)
        dlg = ContentAssistTextEditor(self._grid.kweditor, suggestions, (400, 400))
        dlg._popup.show(600, 400, 20)
        result = dlg._popup.content_assist_for('Log Many')
        shown = dlg.is_shown()
        print(f"DEBUG: test_z_kweditor.py: test_contentassist_text_editor result={result} shown={shown}")
        # assert shown is True
        # Uncomment next lines if you want to see the app
        # wx.CallLater(5000, self.app.ExitMainLoop)
        # self.app.MainLoop()

    def test_contentassist_text_ctrl(self):
        suggestions = SuggestionSource(None, self.app.project.controller)
        dlg = ContentAssistTextCtrl(self._grid.kweditor, suggestions, (400, 400))
        dlg._popup.show(600, 400, 20)
        result = dlg._popup.content_assist_for('Log Many')
        shown = dlg.is_shown()
        print(f"DEBUG: test_z_kweditor.py: test_contentassist_text_ctrl result={result} shown={shown}")
        # assert shown is True
        # Uncomment next lines if you want to see the app
        # wx.CallLater(5000, self.app.ExitMainLoop)
        # self.app.MainLoop()

    # @pytest.mark.skip()
    def test_contentassist_expandotextctrl(self):
        # suggestions = SuggestionSource(None, self.app.project.controller)
        dlg = ExpandingContentAssistTextCtrl(self._grid.kweditor, self.plugin, self.app.project.controller)
        dlg._popup.show(600, 400, 20)
        result = dlg._popup.content_assist_for('Log Many')
        shown = dlg.is_shown()
        print(f"DEBUG: test_z_kweditor.py: test_contentassist_text_ctrl result={result} shown={shown}")
        # assert shown is True
        # Uncomment next lines if you want to see the app
        # wx.CallLater(5000, self.app.ExitMainLoop)
        # self.app.MainLoop()

    def test_contentassist_file_button(self):
        suggestions = SuggestionSource(None, self.app.project.controller)
        dlg = ContentAssistFileButton(self._grid.kweditor, suggestions, 'Browse', self.app.project.controller)
        dlg._popup.show(600, 400, 20)
        result = dlg._popup.content_assist_for('Log Many')
        shown = dlg.is_shown()
        print(f"DEBUG: test_z_kweditor.py: test_contentassist_text_editor result={result} shown={shown}")
        # assert shown is True
        # Uncomment next lines if you want to see the app
        # wx.CallLater(5000, self.app.ExitMainLoop)
        # self.app.MainLoop()

    def test_get_resources(self):
        res = self.creator._only_resource_files(self.app.tree)
        print(f"DEBUG: test_edit_creator.py EditorCreatorTest test_get_resources res={res}")
        # Uncomment next lines if you want to see the app
        # wx.CallLater(5000, self.app.ExitMainLoop)
        # self.app.MainLoop()

    # @pytest.mark.skip()
    # @pytest.mark.skipif(os.sep == '\\', reason="Causes exception on Windows")
    def test_miscellanous(self):
        from robotide.editor.kweditor import requires_focus
        focused = requires_focus(self._grid.kweditor._resize_grid)
        assert focused
        self._grid.kweditor._resize_grid()
        self.settings['Grid'].set('auto size cols', True)
        self._grid.kweditor._resize_grid()
        self.settings['Grid'].set('col size', 100)
        self._grid.kweditor._resize_grid()
        self.settings['Grid'].set('auto size cols', False)
        self._grid.kweditor._resize_grid()
        self.settings['Grid'].set('word wrap', False)
        self._grid.kweditor._resize_grid()

        # Uncomment next lines if you want to see the app
        # wx.CallLater(5000, self.app.ExitMainLoop)
        # self.app.MainLoop()

if __name__ == '__main__':
    unittest.main()
