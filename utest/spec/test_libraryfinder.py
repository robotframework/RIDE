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
import wx
import wx.lib.agw.aui as aui
import shutil
import sys
import unittest

from unittest.mock import patch
from pytest import MonkeyPatch
from wx.lib.agw.aui import AuiManager
from wx.lib.agw.buttonpanel import BoxSizer
from multiprocessing import shared_memory
from utest.resources import datafilereader, MessageRecordingLoadObserver
from robotide.publish import PUBLISHER, RideExecuteLibraryInstall, RideOpenLibraryDocumentation
from robotide.spec.libraryfinder import LibraryFinderPlugin
from robotide.ui.mainframe import ActionRegisterer, ToolBar
from robotide.ui.actiontriggers import MenuBar, ShortcutRegistry
from robotide.application import Project, RIDE
# from robotide.run import ui
from robotide.controller.filecontrollers import (TestCaseFileController, TestDataDirectoryController,
                                                 ResourceFileController)
from robotide.ui.treeplugin import Tree
from robotide.ui.notebook import NoteBook

from robotide.robotapi import Variable
from robotide.controller import data_controller
from robotide.controller.settingcontrollers import VariableController
from robotide.controller.tablecontrollers import VariableTableController
from robotide.editor import EditorPlugin, EditorCreator
from robotide.editor.macroeditors import TestCaseEditor
from robotide.editor.settingeditors import SettingEditor, ImportSettingListEditor
from robotide.editor.editors import EditorPanel
from robotide.editor.customsourceeditor import CodeEditorPanel, SourceCodeEditor
from robotide.namespace import Namespace
from robotide.preferences import RideSettings
from robotide.controller.robotdata import new_test_case_file
from utest.resources import FakeSettings

# Workaround for relative import in non-module
# see https://stackoverflow.com/questions/16981921/relative-imports-in-python-3
PACKAGE_PARENT = '..'
SCRIPT_DIR = os.path.dirname(os.path.realpath(os.path.join(os.getcwd(),
                                              os.path.expanduser(__file__))))
sys.path.append(os.path.normpath(os.path.join(SCRIPT_DIR, PACKAGE_PARENT)))

DATADIR = 'fake'
DATAPATH = '%s/path' % DATADIR
# TestCaseFileEditor._populate = lambda self: None
try:
    from fakeplugin import FakePlugin
except ImportError:  # Python 3
    from ..editor.fakeplugin import FakePlugin

nb_style = aui.AUI_NB_DEFAULT_STYLE | aui.AUI_NB_WINDOWLIST_BUTTON | aui.AUI_NB_TAB_EXTERNAL_MOVE \
           | aui.AUI_NB_SUB_NOTEBOOK | aui.AUI_NB_SMART_TABS


def close_open_dialogs(evt=None):
    lst = wx.GetTopLevelWindows()
    for i in range(len(lst) - 1, 0, -1):
        dialog = lst[i]
        if isinstance(dialog, wx.Dialog):
            print("Closing " + str(dialog))
            wx.CallAfter(dialog.Close)

def side_effect(args=None):
    return -1


class MainFrame(wx.Frame):
    book = None

    def __init__(self):
        wx.Frame.__init__(self, parent=None, title='Grid Editor Test App', size=wx.Size(900, 700))
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
        self.settings.add_section('Plugins')
        main_plugin_section = self.settings['Plugins']
        main_plugin_section.add_section('Library Finder')
        plugin_section = self.settings['Plugins']['Library Finder']
        plugin_section.add_section('AppiumLibrary')
        plugin_section['AppiumLibrary']['documentation'] = \
            'https://serhatbolsu.github.io/robotframework-appiumlibrary/AppiumLibrary.html'
        plugin_section['AppiumLibrary']['command'] = ['%executable -m pip install -U robotframework-appiumlibrary']
        plugin_section.add_section('Browser')
        plugin_section['Browser']['documentation'] = \
            'https://marketsquare.github.io/robotframework-browser/Browser.html'
        plugin_section['Browser']['command'] = ['node -v', '%executable -m pip install -U robotframework-browser',
                   '%executable -m Browser.entry init']
        plugin_section.add_section('CSVLibrary')
        plugin_section['CSVLibrary']['documentation'] = \
            'https://rawgit.com/s4int/robotframework-CSVLibrary/master/doc/CSVLibrary.html'
        plugin_section['CSVLibrary']['command'] = ['%executable -m pip install -U robotframework-csvlibrary']
        plugin_section.add_section('RequestsLibrary')
        plugin_section['RequestsLibrary']['documentation'] = \
            'https://marketsquare.github.io/robotframework-requests/doc/RequestsLibrary.html'
        plugin_section['RequestsLibrary']['command'] = ['%executable -m pip install -U robotframework-requests']
        plugin_section.add_section('NoCommand')
        plugin_section['NoCommand']['documentation'] = 'https://robotframework.org'
        plugin_section.add_section('NoDoc')
        plugin_section['NoDoc']['command'] = ['%executable -m pip list']
        plugin_section.add_section('NoNothing')

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
        mb.take_menu_bar_into_use()
        self._mgr.Update()
        return True

    def _datafile_controller(self):
        return data_controller(new_test_case_file(datafilereader.TESTCASEFILE_WITH_EVERYTHING), self.project)

    def OnExit(self):  # Overrides wx method
        if hasattr(self, 'file_settings'):
            os.remove(self.file_settings)
        self.ExitMainLoop()
        return 0


class TestLibraryFinder(unittest.TestCase):

    def setUp(self):
        self.app = MyApp()
        self.settings = self.app.settings
        try:
            self.shared_mem = shared_memory.ShareableList(['en'], name="language")
        except FileExistsError:  # Other instance created file
            self.shared_mem = shared_memory.ShareableList(name="language")
        self.frame = self.app.frame
        self.frame.actions = ActionRegisterer(AuiManager(self.frame), MenuBar(self.frame), ToolBar(self.frame),
                                              ShortcutRegistry(self.frame))
        self.frame.tree = Tree(self.frame, self.frame.actions, self.settings)
        self.app.project = Project(self.app.namespace, self.app.settings)
        self.app.project.load_datafile(datafilereader.TESTCASEFILE_WITH_EVERYTHING, MessageRecordingLoadObserver())
        self.app.model = self.app.project.data
        self.namespace = self.app.project.namespace
        self.controllers = self.app.project.all_testcases()
        self.test_case = next(self.controllers)
        self.suite = self.app.project.suite
        self.plugin = EditorPlugin(self.app)
        self.plugin.add_self_as_tree_aware_plugin()
        self.app.tree.populate(self.app.project)
        self.panel = EditorPanel(self.plugin, self.frame, self.app.project.controller, self.frame.tree)
        self.source = self.app.tree.controller
        sizer = BoxSizer()
        managed_window = self.app._mgr.GetManagedWindow()  # "notebook_editors"
        managed_window.SetSizer(sizer)
        self._grid = ImportSettingListEditor(self.panel, self.frame.tree, self.app.project.controller.imports)
        self.plugin.add_tab(self._grid, 'Editor')
        self.plugin._editor_component = self._grid  # KeywordEditor(self, self.editor, self.app.tree)
        self.app.tree.set_editor(self.plugin._editor_component)
        self.app.tree.populate(self.app.project)
        self.app.frame.SetStatusText("File:" + self.app.project.data.source)
        self._registered_editors = {}
        self.creator = EditorCreator(self._register)
        self.creator.register_editors()
        self.suite = self.app.project.suite
        self.imports = [i for i in self.suite.imports]  # .imports
        # Uncomment next line (and MainLoop in tests) if you want to see the app
        self.frame.Show()
        self.SHOWING = True
        self.frame.Center()
        self.libplugin = LibraryFinderPlugin(self.app)
        # self.frame.notebook = self.app.notebook
        self.libplugin._editor_component = self._grid
        self.libplugin.enable()
        self.libplugin._editor_component.SetSize(wx.Size(800, 600))
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
        return data_controller(new_test_case_file(datafilereader.TESTCASEFILE_WITH_EVERYTHING), self.app.project)

    def tearDown(self):
        self.libplugin.disable()
        self.libplugin.unsubscribe_all()
        PUBLISHER.unsubscribe_all()
        self.app.project.close()
        wx.CallAfter(self.app.ExitMainLoop)
        # DEBUG self.app.MainLoop()  # With this here, there is no Segmentation fault
        # wx.CallAfter(wx.Exit)
        self.shared_mem.shm.close()
        self.shared_mem.shm.unlink()
        self.app.Destroy()
        self.app = None
        if os.path.exists(DATADIR):
            shutil.rmtree(DATADIR, ignore_errors=True)

    def test_call_plugin_exec_install(self):
        from time import sleep
        wx.CallLater(8000, self.app.ExitMainLoop)
        wx.CallLater(5000, close_open_dialogs)
        RideExecuteLibraryInstall(item=None).publish()
        sleep(1)
        wx.CallLater(6000, close_open_dialogs)
        RideExecuteLibraryInstall(item="AppiumLibrary").publish()
        self.libplugin._execute_namespace_update()
        command = self.libplugin.find_install_command(None)
        assert command == []
        command = self.libplugin.find_install_command("NonExisting")
        assert command == []
        command = self.libplugin.find_install_command("NoCommand")
        assert command == []
        command = self.libplugin.find_install_command("NoDoc")
        assert command == ['%executable -m pip list']
        command = self.libplugin.find_install_command("NoNothing")
        assert command == []
        command = self.libplugin.find_install_command("AppiumLibrary")
        assert command == ['%executable -m pip install -U robotframework-appiumlibrary']

    @patch('wx.LaunchDefaultBrowser')
    def test_call_plugin_doc(self, mock_input):
        from time import sleep
        wx.CallLater(8000, self.app.ExitMainLoop)
        wx.CallLater(5000, close_open_dialogs)
        RideOpenLibraryDocumentation(item=None).publish()
        sleep(1)
        wx.CallLater(6000, close_open_dialogs)
        RideOpenLibraryDocumentation(item="RequestsLibrary").publish()
        documentation = self.libplugin.find_documentation_url(None)
        assert documentation == ''
        documentation = self.libplugin.find_documentation_url("NonExisting")
        assert documentation == ''
        documentation = self.libplugin.find_documentation_url("NoDoc")
        assert documentation == ''
        documentation = self.libplugin.find_documentation_url("NoNothing")
        assert documentation == ''
        documentation = self.libplugin.find_documentation_url("NoCommand")
        assert documentation == 'https://robotframework.org'
        documentation = self.libplugin.find_documentation_url("RequestsLibrary")
        assert documentation == 'https://marketsquare.github.io/robotframework-requests/doc/RequestsLibrary.html'
        documentation = self.libplugin.find_documentation_url("Remote")
        assert documentation == 'https://github.com/robotframework/RemoteInterface'
        documentation = self.libplugin.find_documentation_url("Collections")
        assert documentation == 'https://robotframework.org/robotframework/latest/libraries/Collections.html'

    @patch('robotide.run.ui.Runner')
    def test_misc_run_install(self, mock_input):
        wx.CallLater(6000, self.app.ExitMainLoop)
        result = self.libplugin.run_install('NoDoc', ['%executable -m pip list'])
        assert result

    def test_misc_fail_run(self):
        from robotide.run import ui
        wx.CallLater(6000, self.app.ExitMainLoop)
        with MonkeyPatch().context() as m:
            m.setattr(ui.Runner, 'run', side_effect)
            result = self.libplugin.run_install('NoDoc', ['%executable -m pip list'])
            assert not result

    def test_parser(self):
        wx.CallLater(6000, self.app.ExitMainLoop)
        self.app.settings.__delattr__('executable')
        exe = sys.executable
        result = self.libplugin.parse_command(['%executable -m pip list'])
        assert result == [f'{exe} -m pip list']
        self.app.settings['executable'] = 'my_python_executable'
        result = self.libplugin.parse_command(['%executable -m pip list'])
        assert result == ['my_python_executable -m pip list']
        result = self.libplugin.parse_command(['some command without python', '%executable -m pip list',
                                               '%executable --version'])
        assert result == ['some command without python', 'my_python_executable -m pip list',
                          'my_python_executable --version']


if __name__ == '__main__':
    unittest.main()
