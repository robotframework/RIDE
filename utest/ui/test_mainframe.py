#  Copyright 2024-     Robot Framework Foundation
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
import os
import pytest

DISPLAY = os.getenv('DISPLAY')
if not DISPLAY:  # Avoid failing unit tests in system without X11
    pytest.skip("Skipped because of missing DISPLAY", allow_module_level=True)
import wx
from wx.lib.agw.aui import AuiManager

from robotide.robotapi import (TestDataDirectory, TestCaseFile, ResourceFile,
                               TestCase, UserKeyword)
from robotide.spec.librarymanager import LibraryManager
from robotide.ui.mainframe import ActionRegisterer, ToolBar
from robotide.ui.actiontriggers import MenuBar, ShortcutRegistry
from robotide.application import Project
from robotide.application.pluginloader import PluginLoader
from robotide.controller.filecontrollers import (TestDataDirectoryController, ResourceFileController)
from utest.resources import FakeSettings
from robotide.editor.texteditor import TextEditorPlugin
from robotide.log import LogPlugin
from robotide.ui import mainframe
from robotide.publish import PUBLISHER
from robotide.ui.treeplugin import Tree
from robotide.namespace.namespace import Namespace


app = wx.App()


class _BaseDialogTest(unittest.TestCase):

    def setUp(self):
        self.app = wx.App()
        self.app.settings = FakeSettings()
        font_size = self.app.settings['General'].get('font size', 12)
        font_face = self.app.settings['General'].get('font face', 'Helvetica')
        self.app.fontinfo = wx.FontInfo(font_size).FaceName(font_face).Bold(False)
        self.app.namespace = Namespace(FakeSettings())
        self.model = self._create_model()
        self.frame = mainframe.RideFrame(self.app, self.model)
        self.app.frame = self.frame
        txtplugin = TextEditorPlugin
        logplugin = LogPlugin
        plugins_dir = [os.path.join(os.path.dirname(__file__), 'plugins_for_loader')]
        self.loader = PluginLoader(self.app, plugins_dir, [txtplugin, logplugin])
        self.app.get_plugins = lambda: self.loader.plugins
        self.frame.tree = Tree(self.frame, ActionRegisterer(AuiManager(self.frame),
                                                            MenuBar(self.frame), ToolBar(self.frame),
                                                            ShortcutRegistry(self.frame)), self.app.settings)
        # self.frame.Show()

    def tearDown(self):
        PUBLISHER.unsubscribe_all()
        self.app.ExitMainLoop()
        self.app.Destroy()
        self.app = None
        # app.MainLoop()  # With this here, there is no Segmentation fault

    def _create_model(self):
        suite = self._create_directory_suite('/top_suite')
        suite.children = [self._create_file_suite('sub_suite_%d.robot' % i)
                          for i in range(3)]
        res = ResourceFile()
        res.source = 'resource.robot'
        res.keyword_table.keywords.append(UserKeyword(res, 'Resource Keyword', ['en']))
        library_manager = LibraryManager(':memory:')
        library_manager.create_database()
        model = Project(self.app.namespace, library_manager=library_manager)
        model.controller = TestDataDirectoryController(suite)
        rfc = ResourceFileController(res, project=model)
        model.resources.append(rfc)
        model.insert_into_suite_structure(rfc)
        return model

    def _create_directory_suite(self, source):
        return self._create_suite(TestDataDirectory, source, is_dir=True)

    def _create_file_suite(self, source):
        suite = self._create_suite(TestCaseFile, source)
        suite.testcase_table.tests = [TestCase(suite, '%s Fake Test %d' % (suite.name, i)) for i in range(16)]
        return suite

    @staticmethod
    def _create_suite(suite_class, source, is_dir=False):
        suite = suite_class()
        suite.source = source
        if is_dir:
            suite.directory = source
        suite.keyword_table.keywords = [UserKeyword(suite.keyword_table, '%s Fake UK %d' % (suite.name, i),
                                                    ['en'])
            for i in range(5)]
        return suite


class TestMainFrame(_BaseDialogTest):

   def test_show_mainframe(self):
       self.frame.Show()
       wx.CallLater(2000, self.app.ExitMainLoop)
       self.app.MainLoop()

   def test_show_plugins_manager(self):
        self.frame.Show()
        plugins = self.loader.plugins
        self.frame._plugin_manager.show(plugins)
        wx.CallLater(5000, self.app.ExitMainLoop)
        wx.CallLater(4000, self.frame._plugin_manager._panel.Close)
        self.app.MainLoop()


if __name__ == '__main__':
    unittest.main()
    app.Destroy()
