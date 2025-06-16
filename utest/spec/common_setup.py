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
from robotide.application import RIDE
from robotide.ui.notebook import NoteBook
from robotide.namespace import Namespace
from robotide.preferences import RideSettings
from utest.resources import FakeSettings, datafilereader
from robotide.ui.mainframe import ActionRegisterer, ToolBar
from robotide.ui.actiontriggers import MenuBar, ShortcutRegistry
from robotide.ui.treeplugin import Tree
from robotide.controller import data_controller
from robotide.controller.robotdata import new_test_case_file

nb_style = aui.AUI_NB_DEFAULT_STYLE | aui.AUI_NB_WINDOWLIST_BUTTON | aui.AUI_NB_TAB_EXTERNAL_MOVE \
           | aui.AUI_NB_SUB_NOTEBOOK | aui.AUI_NB_SMART_TABS


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

    def __init__(self, path=None, updatecheck=False, settingspath=None):
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
