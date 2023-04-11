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
from robotide.publish import PUBLISHER, RideSuiteAdded, RideNotebookTabChanging
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
        self.plugin._editor_component = texteditor.SourceEditor(self.app.book, self.plugin.title,
                                                                texteditor.DataValidationHandler(self.plugin))
        self.plugin.enable()
        self.app.project.load_datafile(datafilereader.TESTCASEFILE_WITH_EVERYTHING, MessageRecordingLoadObserver())
        self.app.tree.set_editor(self.plugin._editor_component)
        self.app.tree.populate(self.app.project)
        self.app.frame.SetStatusText("File:" + self.app.project.data.source)
        # Uncomment next line (and MainLoop in tests) if you want to see the app
        # self.frame.Show()

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
        """
        self.app.project.load_datafile(datafilereader.TESTCASEFILE_WITH_EVERYTHING, MessageRecordingLoadObserver())
        print(f"DEBUG: project source={self.app.project.data.source} plugin={self.plugin.name}")
        print(f"DEBUG: project is_focused={self.plugin._editor.is_focused()} plugin enabled? "
              f"{self.plugin.initially_enabled}")
        print(f"DEBUG: project datafile={self.plugin.get_selected_datafile()}")
        print(f"DEBUG: selected datafile_controller={self.app.tree.get_selected_datafile_controller()}")
        item = self.app.tree.GetFirstVisibleItem()
        self.app.tree.SelectItem(item)
        self.app.tree.OnSelection(None)
        self.plugin._tree = self.app.tree
        frompl = self.plugin.tree.GetFirstVisibleItem()
        print(f"DEBUG: tree first item_text={item.GetText()} item_data={item.GetData()}")
        print(f"DEBUG: from plugin frompl={frompl.GetText()} frompl_data={frompl.GetData()}")
        """
        self.plugin._editor_component._editor.set_text("Hello World!")
        # print(f"DEBUG: editor is_focused={self.plugin._editor_component.is_focused()}")
        self.plugin._editor_component.insert_row(None)
        fulltext = self.plugin._editor_component._editor.GetText()
        assert fulltext == "\nHello World!"
        # Uncomment next lines if you want to see the app
        # wx.CallLater(5000, self.app.ExitMainLoop)
        # self.app.MainLoop()

    def test_delete_row_single(self):
        self.plugin._editor_component._editor.set_text("\nHello World!")
        self.plugin._editor_component.delete_row(None)
        fulltext = self.plugin._editor_component._editor.GetText()
        assert fulltext == "Hello World!"
        # Uncomment next lines if you want to see the app
        # wx.CallLater(5000, self.app.ExitMainLoop)
        # self.app.MainLoop()

    def test_tab_change_and_is_focused(self):
        RideNotebookTabChanging(oldtab='Text Edit', newtab='Editor').publish()
        assert not self.plugin._editor_component.is_focused()
        RideNotebookTabChanging(oldtab='Editor', newtab='Text Edit').publish()
        assert self.plugin._editor_component.is_focused()
        # Uncomment next lines if you want to see the app
        # wx.CallLater(5000, self.app.ExitMainLoop)
        # self.app.MainLoop()

    def test_move_row_up(self):
        content = ['1 - Line one\n', '2 - Line two\n', '3 - Line three\n']
        self.plugin._editor_component._editor.set_text(''.join(content))
        pos = len('1 - Line one\n')
        self.plugin._editor_component._editor.SetSelection(pos+1, pos+4)
        self.plugin._editor_component.move_row_up(None)
        fulltext = self.plugin._editor_component._editor.GetText()
        assert fulltext == content[1] + content[0] + content[2]
        # Uncomment next lines if you want to see the app
        # wx.CallLater(5000, self.app.ExitMainLoop)
        # self.app.MainLoop()

    def test_move_row_down(self):
        content = ['1 - Line one\n', '2 - Line two\n', '3 - Line three\n']
        self.plugin._editor_component._editor.set_text(''.join(content))
        pos = len('1 - Line one\n')
        self.plugin._editor_component._editor.SetSelection(pos+1, pos+4)
        self.plugin._editor_component.move_row_down(None)
        fulltext = self.plugin._editor_component._editor.GetText()
        assert fulltext == content[0] + content[2] + content[1]
        # Uncomment next lines if you want to see the app
        # wx.CallLater(5000, self.app.ExitMainLoop)
        # self.app.MainLoop()

    def test_execute_comment(self):
        content = ['1 - Line one\n', '2 - Line two\n', '3 - Line three\n']
        self.plugin._editor_component._editor.set_text(''.join(content))
        pos = len('1 - Line one\n')
        spaces = ' ' * self.plugin._editor_component._tab_size
        self.plugin._editor_component._editor.SetSelection(pos+1, pos+4)
        self.plugin._editor_component.execute_comment(None)
        fulltext = self.plugin._editor_component._editor.GetText()
        assert fulltext == content[0] + 'Comment' + spaces + content[1] + content[2]
        # print(f"DEBUG: fulltext:\n{fulltext}")
        # Uncomment next lines if you want to see the app
        # wx.CallLater(5000, self.app.ExitMainLoop)
        # self.app.MainLoop()

    def test_execute_uncomment(self):
        pos = len('1 - Line one\n')
        spaces = ' ' * self.plugin._editor_component._tab_size
        content = ['1 - Line one\n', '2 - Line two\n', '3 - Line three\n']
        self.plugin._editor_component._editor.set_text(content[0] + 'Comment' + spaces + content[1] + content[2])
        self.plugin._editor_component._editor.SetSelection(pos+1, pos+4)
        self.plugin._editor_component.execute_uncomment(None)
        fulltext = self.plugin._editor_component._editor.GetText()
        assert fulltext == content[0] + content[1] + content[2]
        # print(f"DEBUG: fulltext:\n{fulltext}")
        # Uncomment next lines if you want to see the app
        # wx.CallLater(5000, self.app.ExitMainLoop)
        # self.app.MainLoop()

    def test_insert_cell_two_lines(self):
        spaces = ' ' * self.plugin._editor_component._tab_size
        content = [spaces + '1 - Line one\n', spaces + '2 - Line two\n', spaces + '3 - Line three\n']
        pos = len(content[0])
        self.plugin._editor_component._editor.set_text(''.join(content))
        self.plugin._editor_component._editor.SetAnchor(len(spaces) + pos + 2)
        self.plugin._editor_component._editor.SetSelection(0, pos + 2)
        self.plugin._editor_component.insert_cell(None)
        fulltext = self.plugin._editor_component._editor.GetText()
        # print(f"DEBUG: fulltext:\n{fulltext}")
        assert fulltext == spaces + content[0] + spaces + content[1] + content[2]
        # Uncomment next lines if you want to see the app
        # wx.CallLater(5000, self.app.ExitMainLoop)
        # self.app.MainLoop()

    def test_insert_cell_no_selection(self):
        spaces = ' ' * self.plugin._editor_component._tab_size
        content = [spaces + '1 - Line one' + spaces + 'with cells' + spaces + 'last text\n']
        pos = len(spaces + '1 - Line one' + spaces) + 1
        self.plugin._editor_component._editor.set_text(''.join(content))
        self.plugin._editor_component._editor.SetAnchor(pos)
        self.plugin._editor_component._editor.SetSelection(pos, pos)
        self.plugin._editor_component.insert_cell(None)
        fulltext = self.plugin._editor_component._editor.GetText()
        # print(f"DEBUG: fulltext:\n{fulltext}")
        assert fulltext == spaces + '1 - Line one' + spaces + spaces + 'with cells' + spaces + 'last text\n'
        # Uncomment next lines if you want to see the app
        # wx.CallLater(5000, self.app.ExitMainLoop)
        # self.app.MainLoop()

    def test_insert_cell_with_selection(self):
        spaces = ' ' * self.plugin._editor_component._tab_size
        content = [spaces + '1 - Line one' + spaces + 'with cells' + spaces + 'last text\n']
        pos = len(spaces + '1 - Line one' + spaces + 'with cells' + spaces)
        self.plugin._editor_component._editor.set_text(''.join(content))
        self.plugin._editor_component._editor.SetAnchor(pos + 6)
        self.plugin._editor_component._editor.SetSelection(pos, pos + 6)
        self.plugin._editor_component.insert_cell(None)
        fulltext = self.plugin._editor_component._editor.GetText()
        # print(f"DEBUG: fulltext:\n{fulltext}")
        assert fulltext == spaces + '1 - Line one' + spaces + 'with cells' + spaces + spaces + 'last text\n'
        # Uncomment next lines if you want to see the app
        # wx.CallLater(5000, self.app.ExitMainLoop)
        # self.app.MainLoop()

    def test_delete_cell(self):
        spaces = ' ' * self.plugin._editor_component._tab_size
        content = [spaces + '1 - Line one' + spaces + 'with cells' + spaces + 'last text\n']
        pos = len(spaces + '1 - Line one' + spaces + 'with cells')
        self.plugin._editor_component._editor.set_text(''.join(content))
        self.plugin._editor_component._editor.SetAnchor(pos)
        self.plugin._editor_component._editor.SetSelection(pos - len('with cells'), pos)
        self.plugin._editor_component.delete_cell(None)
        fulltext = self.plugin._editor_component._editor.GetText()
        # print(f"DEBUG: fulltext:\n{fulltext}")
        assert fulltext == spaces + '1 - Line one' + spaces + 'last text\n'
        # Uncomment next lines if you want to see the app
        # wx.CallLater(5000, self.app.ExitMainLoop)
        # self.app.MainLoop()

    def test_execute_sharp_comment_two_lines(self):
        spaces = ' ' * self.plugin._editor_component._tab_size
        content = [spaces, '1 - Line one\n', spaces, '2 - Line two\n', spaces, '3 - Line three\n']
        end = len(spaces + content[1])
        self.plugin._editor_component._editor.set_text(''.join(content))
        self.plugin._editor_component._editor.SetAnchor(len(spaces) + end + len(spaces + content[3]) - 1)
        self.plugin._editor_component._editor.SetSelection(len(spaces), end + len(spaces + content[3]) - 1)
        self.plugin._editor_component.execute_sharp_comment(None)
        fulltext = self.plugin._editor_component._editor.GetText()
        print(f"DEBUG: fulltext:\n{fulltext}")
        assert fulltext == spaces + '# ' + content[1] + spaces + '# ' + content[3] + spaces + content[5]
        # Uncomment next lines if you want to see the app
        # wx.CallLater(5000, self.app.ExitMainLoop)
        # self.app.MainLoop()

    def test_execute_sharp_comment_no_selection(self):
        spaces = ' ' * self.plugin._editor_component._tab_size
        content = [spaces + '1 - Line one' + spaces + 'with cells' + spaces + 'last text\n']
        pos = len(spaces + '1 - Line one' + spaces+ 'with cells')
        self.plugin._editor_component._editor.set_text(''.join(content))
        self.plugin._editor_component._editor.SetAnchor(pos)
        self.plugin._editor_component._editor.SetSelection(pos, pos)
        self.plugin._editor_component.execute_sharp_comment(None)
        fulltext = self.plugin._editor_component._editor.GetText()
        print(f"DEBUG: fulltext:\n{fulltext}")
        assert fulltext == spaces + '# ' + '1 - Line one' + spaces + 'with cells' + spaces + 'last text\n'
        # Uncomment next lines if you want to see the app
        # wx.CallLater(5000, self.app.ExitMainLoop)
        # self.app.MainLoop()

    def test_execute_sharp_comment_with_selection(self):
        spaces = ' ' * self.plugin._editor_component._tab_size
        content = [spaces + '1 - Line one' + spaces + 'with cells' + spaces + 'last text\n']
        pos = len(spaces + '1 - Line one' + spaces+ 'with cells')
        self.plugin._editor_component._editor.set_text(''.join(content))
        self.plugin._editor_component._editor.SetAnchor(pos)
        self.plugin._editor_component._editor.SetSelection(pos - len('with cells'), pos)
        self.plugin._editor_component.execute_sharp_comment(None)
        fulltext = self.plugin._editor_component._editor.GetText()
        # print(f"DEBUG: fulltext:\n{fulltext}")
        assert fulltext == spaces + '1 - Line one' + spaces + '# ' + 'with cells' + spaces + 'last text\n'
        # Uncomment next lines if you want to see the app
        # wx.CallLater(5000, self.app.ExitMainLoop)
        # self.app.MainLoop()

    def test_execute_sharp_uncomment_two_lines(self):
        spaces = ' ' * self.plugin._editor_component._tab_size
        content = [spaces + '# ', '1 - Line one\n', spaces + '# ', '2 - Line two\n', spaces, '3 - Line three\n']
        end = len(spaces + content[1])
        self.plugin._editor_component._editor.set_text(''.join(content))
        self.plugin._editor_component._editor.SetAnchor(len(spaces) + end + len(spaces + content[3]) - 1)
        self.plugin._editor_component._editor.SetSelection(len(spaces), end + len(spaces + content[3]) - 1)
        self.plugin._editor_component.execute_sharp_uncomment(None)
        fulltext = self.plugin._editor_component._editor.GetText()
        # print(f"DEBUG: fulltext:\n{fulltext}")
        assert fulltext == spaces + content[1] + spaces + content[3] + spaces + content[5]
        # Uncomment next lines if you want to see the app
        # wx.CallLater(5000, self.app.ExitMainLoop)
        # self.app.MainLoop()

    def test_execute_sharp_uncomment_no_selection(self):
        spaces = ' ' * self.plugin._editor_component._tab_size
        content = [spaces + '# ' + '1 - Line one' + spaces + 'with cells' + spaces + 'last text\n']
        pos = len(spaces + '1 - Line one' + spaces+ 'with cells')
        self.plugin._editor_component._editor.set_text(''.join(content))
        self.plugin._editor_component._editor.SetAnchor(pos)
        self.plugin._editor_component._editor.SetSelection(pos, pos)
        self.plugin._editor_component.execute_sharp_uncomment(None)
        fulltext = self.plugin._editor_component._editor.GetText()
        # print(f"DEBUG: fulltext:\n{fulltext}")
        assert fulltext == spaces + '1 - Line one' + spaces + 'with cells' + spaces + 'last text\n'
        # Uncomment next lines if you want to see the app
        # wx.CallLater(5000, self.app.ExitMainLoop)
        # self.app.MainLoop()

    def test_execute_sharp_uncomment_with_selection(self):
        spaces = ' ' * self.plugin._editor_component._tab_size
        content = [spaces + '1 - Line one' + spaces + '# ' + 'with cells' + spaces + 'last text\n']
        pos = len(spaces + '1 - Line one' + spaces + '# ' + 'with cells')
        self.plugin._editor_component._editor.set_text(''.join(content))
        self.plugin._editor_component._editor.SetAnchor(pos)
        self.plugin._editor_component._editor.SetSelection(pos - len('with cells'), pos)
        self.plugin._editor_component.execute_sharp_uncomment(None)
        fulltext = self.plugin._editor_component._editor.GetText()
        # print(f"DEBUG: fulltext:\n{fulltext}")
        assert fulltext == spaces + '1 - Line one' + spaces + 'with cells' + spaces + 'last text\n'
        # Uncomment next lines if you want to see the app
        # wx.CallLater(5000, self.app.ExitMainLoop)
        # self.app.MainLoop()


if __name__ == '__main__':
    unittest.main()

