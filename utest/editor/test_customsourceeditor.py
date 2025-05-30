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
import re
import subprocess
import sys
import time

import psutil
import pytest
import unittest
import wx

from utest.resources import datafilereader, FakeSettings
from robotide.editor.customsourceeditor import SourceCodeEditor, PythonSTC, main

PLUGIN_NAME = "Text Edit"


class TestSourceCodeEditor(unittest.TestCase):

    def setUp(self):
        self.app = wx.App()
        self._settings = FakeSettings()
        self._settings.add_section(PLUGIN_NAME)
        self.tab_markers = self._settings[PLUGIN_NAME].get('tab markers', True)
        self.fold_symbols = self._settings[PLUGIN_NAME].get('fold symbols', 2)
        self.frame = wx.Frame(None)
        # Uncomment next line (and MainLoop in tests) if you want to see the app
        # self.frame.Show()

    def tearDown(self):
        self.app.ExitMainLoop()
        self.app.Destroy()
        self.app = None

    @pytest.mark.skip("Does not return")
    def test_call_main_with_frame(self):
        self.frame.Show()
        wx.CallLater(5000, self.frame.Destroy)
        wx.CallLater(6000, self.app.ExitMainLoop)
        main(datafilereader.TESTCASEFILE_WITH_EVERYTHING, self.frame)
        # Uncomment next lines if you want to see the app
        # wx.CallLater(5000, self.app.ExitMainLoop)
        # self.app.MainLoop()

    def test_call_source_editor(self):
        # PythonSTC.__init__(self, parent, -1, options={'tab markers':self.tab_markers, 'fold symbols':self.fold_symbols},
        #                    style=style)
        self.frame.SetSize(wx.Rect((800, 600)))
        wx.CallLater(8000, self.frame.Destroy)
        wx.CallLater(10000, self.app.ExitMainLoop)
        self.panel = wx.Panel(self.frame, size=wx.Size(800, 600))
        # self.panel.Center()
        with open(datafilereader.TESTCASEFILE_WITH_EVERYTHING, "r") as fp:
            content = fp.read()
        self.editor = SourceCodeEditor(self.panel, options={'tab markers': True, 'fold symbols': 2})
        self.editor.SetUpEditor()
        self.editor.SetValue(content)
        self.editor.SetEditable(True)
        self.editor.Fit()
        self.editor.Clear()
        print(f"DEBUG test_customsourceeditor.py modified={self.editor.IsModified()}")
        self.editor.SetValue(content)
        self.editor.SetEditable(False)
        self.frame.Show()
        self.frame.Center()
        self.editor.SetInsertionPoint(600)
        self.editor.ShowPosition(800)
        # Uncomment next lines if you want to see the app
        # wx.CallLater(5000, self.app.ExitMainLoop)
        self.app.MainLoop()


if __name__ == '__main__':
    unittest.main()
