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
import os.path

import pytest
import tempfile
import unittest
import wx

from utest.resources import datafilereader, FakeSettings
from robotide.editor.customsourceeditor import SourceCodeEditor, CodeEditorPanel, PythonSTC, main

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
        modified = self.editor.IsModified()
        # print(f"DEBUG test_customsourceeditor.py modified={self.editor.IsModified()}")
        assert modified
        self.editor.SetValue(content)
        self.editor.SetEditable(False)
        self.frame.Show()
        self.frame.Center()
        self.editor.SetInsertionPoint(600)
        self.editor.ShowPosition(800)
        result = self.editor.GetLastPosition()
        # print(f"DEBUG test_customsourceeditor.py GetLastPosition={result}")
        assert result == 1937
        result = self.editor.GetPositionFromLine(30)
        # print(f"DEBUG test_customsourceeditor.py GetPositionFromLine={result}")
        assert result == 1268
        result = self.editor.GetRange(600, 800)
        # print(f"DEBUG test_customsourceeditor.py GetRange={result}")
        assert result == """   PathResource.robot
Resource          resuja/resource.robot
Resource          spec_resource.html
Resource          ${RES_PATH}/another_resource.robot
Resource          ${RES_PATH}/more_resources/${R"""
        self.editor.SetSelection(600, 800)
        result = self.editor.GetSelection()
        # print(f"DEBUG test_customsourceeditor.py GetSelection={result}")
        assert result == (600, 800)
        self.editor.SelectLine(30)
        result = self.editor.GetSelection()
        # print(f"DEBUG test_customsourceeditor.py GetSelection from Line 30={result}")
        assert result == (1268, 1287)
        # Uncomment next lines if you want to see the app
        # self.app.MainLoop()


class TestCodeEditorPanel(unittest.TestCase):

    def setUp(self):
        self.app = wx.App()
        self._settings = FakeSettings()
        self._settings.add_section(PLUGIN_NAME)
        self.tab_markers = self._settings[PLUGIN_NAME].get('tab markers', True)
        self.fold_symbols = self._settings[PLUGIN_NAME].get('fold symbols', 2)
        self.frame = wx.Frame(None)
        self.wkpath = None
        # Uncomment next line (and MainLoop in tests) if you want to see the app
        # self.frame.Show()

    def tearDown(self):
        self.app.ExitMainLoop()
        self.app.Destroy()
        self.app = None
        if self.wkpath and os.path.exists(self.wkpath):
            os.remove(self.wkpath)

    def test_call_code_editor_panel(self):
        # PythonSTC.__init__(self, parent, -1, options={'tab markers':self.tab_markers, 'fold symbols':self.fold_symbols},
        #                    style=style)
        self.frame.SetSize(wx.Rect((900, 800)))
        wx.CallLater(8000, self.frame.Destroy)
        wx.CallLater(10000, self.app.ExitMainLoop)
        # self.panel = wx.Panel(self.frame, size=wx.Size(800, 600))
        # self.panel.Center()
        with open(datafilereader.TESTCASEFILE_WITH_EVERYTHING, "r") as fp:
            content = fp.read()
        with tempfile.NamedTemporaryFile(delete=False, delete_on_close=False) as workfile:
            workfile.write(content.encode('utf-8'))
            workfile.close()
            self.wkpath = workfile.name
        self.editorpanel = CodeEditorPanel(self.frame, None, self.wkpath)
        self.frame.Show()
        self.frame.Center()
        self.editorpanel.Show()
        modified = self.editorpanel.editor.IsModified()
        # print(f"DEBUG test_customsourceeditor.py modified={self.editorpanel.IsModified()}")
        assert modified
        self.editorpanel.on_code_modified(None)
        assert self.editorpanel.btnSave.IsEnabled()
        self.editorpanel.LoadFile(self.wkpath)
        self.editorpanel.JumpToLine(30, True)
        self.editorpanel.on_save(None, self.wkpath)
        modified = self.editorpanel.editor.IsModified()
        print(f"DEBUG test_customsourceeditor.py modified={modified}")
        # assert not modified
        assert not self.editorpanel.btnSave.IsEnabled()
        # Uncomment next lines if you want to see the app
        # self.app.MainLoop()


class KeyEvent:

    def __init__(self, keycode, control=False, shift=False):
        self.keycode = keycode
        self.control = control
        self.shift = shift

    def GetKeyCode(self):
        return self.keycode

    def ControlDown(self):
        return self.control

    def ShiftDown(self):
        return self.shift

    def Skip(self):
        return True


class FoldEvent:

    def __init__(self, control=False, shift=False):
        self.control = control
        self.shift = shift

    def GetModificationType(self):
        return 0

    def GetMargin(self):
        return 2

    def GetShift(self):
        return self.shift

    def GetControl(self):
        return self.control

    def GetPosition(self):
        return 805


class TestPythonCodeEditor(unittest.TestCase):

    def setUp(self):
        self.app = wx.App()
        self.frame = wx.Frame(None)
        # Uncomment next line (and MainLoop in tests) if you want to see the app
        # self.frame.Show()

    def tearDown(self):
        self.app.ExitMainLoop()
        self.app.Destroy()
        self.app = None

    def test_call_python_editor(self):
        self.frame.SetSize(wx.Rect((900, 800)))
        wx.CallLater(8000, self.frame.Destroy)
        wx.CallLater(10000, self.app.ExitMainLoop)
        # self.panel = wx.Panel(self.frame, size=wx.Size(800, 600))
        # self.panel.Center()
        with open(datafilereader.TESTCASEFILE_WITH_EVERYTHING, "r") as fp:
            content = fp.read()
        for style in range(4):
            self.editor = PythonSTC(self.frame, -1, options={'tab markers': True, 'fold symbols': style})
        self.editor.SetSize(wx.Size(800, 600))
        self.editor.SetValue(content)
        self.editor.SetEditable(True)
        self.editor.Fit()
        self.editor.Clear()
        modified = self.editor.IsModified()
        # print(f"DEBUG test_customsourceeditor.py modified={self.editor.IsModified()}")
        assert modified
        self.editor.SetValue(content)
        self.editor.SetEditable(False)
        self.editor.Fit()
        self.editor.on_update_ui(None)
        self.frame.Show()
        self.frame.Center()
        self.editor.SetInsertionPoint(600)
        self.editor.ShowPosition(800)
        # Uncomment next lines if you want to see the app
        # self.app.MainLoop()

    def test_other_calls_python_editor(self):
        self.frame.SetSize(wx.Rect((900, 800)))
        wx.CallLater(10000, self.app.ExitMainLoop)
        with open(datafilereader.TESTCASEFILE_WITH_EVERYTHING, "r") as fp:
            content = fp.read()
        self.editor = PythonSTC(self.frame, -1, options={'tab markers': True, 'fold symbols': 2})
        self.editor.SetSize(wx.Size(800, 600))
        self.editor.SetValue(content)
        self.editor.SetEditable(True)
        self.editor.Fit()
        self.frame.Show()
        self.frame.Center()
        self.editor.SetInsertionPoint(600)
        self.editor.ShowPosition(600)
        for key in "exit()"[:]:
            self.editor.on_key_pressed(KeyEvent(ord(key)))
            # print(f"DEBUG test_customsourceeditor.py on_key_pressed={key} ord(k)={ord(key)}")
            self.editor.on_update_ui(None)
        self.editor.SetInsertionPoint(650)
        self.editor.ShowPosition(650)
        self.editor.on_key_pressed(KeyEvent(ord(' '), True, True))
        self.editor.SetInsertionPoint(700)
        self.editor.ShowPosition(700)
        for key in "zzzz["[:]:
            self.editor.on_key_pressed(KeyEvent(ord(key)))
            self.editor.on_update_ui(None)
        self.editor.on_key_pressed(KeyEvent(ord(' '), True, False))
        self.editor.on_margin_click(FoldEvent())
        self.editor.SetInsertionPoint(800)
        self.editor.ShowPosition(800)
        self.editor.on_key_pressed(KeyEvent(ord('+')))
        self.editor.on_margin_click(FoldEvent(True, True))
        self.editor.FoldAll()
        self.editor.Expand(800, False, False, 1)
        self.editor.Expand(800, True, False, 2, 1)
        self.editor.Expand(800, False, True, 0, 1)
        self.editor.Expand(800, True, True, 2, 1)
        # Uncomment next lines if you want to see the app
        self.app.MainLoop()


if __name__ == '__main__':
    unittest.main()
