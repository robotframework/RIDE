#  Copyright 2008-2009 Nokia Siemens Networks Oyj
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

import wx

from contentassist import ContentAssistTextCtrl
from grid import GridEditor


class ValueEditor(wx.Panel):
    expand_factor = 1
    _sizer_flags_for_editor = wx.ALL

    def __init__(self, parent, value, label=None, validator=None):
        wx.Panel.__init__(self, parent)
        self._sizer = wx.BoxSizer(wx.VERTICAL)
        self._create_editor(value, label)
        if validator:
            self.set_validator(validator)
        self.SetSizer(self._sizer)

    def _create_editor(self, value, label):
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        if label:
            sizer.Add(wx.StaticText(self, label=label, size=(80,-1)), 0, wx.ALL, 5)
        self._editor = self._get_text_ctrl()
        self._editor.AppendText(value)
        sizer.Add(self._editor, 1, self._sizer_flags_for_editor, 3)
        self._sizer.Add(sizer, 1, wx.EXPAND)

    def _get_text_ctrl(self):
        return wx.TextCtrl(self, size=(600,-1))

    def set_validator(self, validator):
        self._editor.SetValidator(validator)

    def get_value(self):
        return self._editor.GetValue()

    def set_focus(self):
        self._editor.SetFocus()


class ListValueEditor(ValueEditor):
    expand_factor = 3
    _sizer_flags_for_editor = wx.ALL|wx.EXPAND

    def _create_editor(self, value, label):
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self._create_label_and_add_button(label))
        self._editor = _EditorGrid(self, value)
        sizer.Add(self._editor, 1, self._sizer_flags_for_editor, 3)
        self._sizer.Add(sizer, 1, wx.EXPAND)

    def _create_label_and_add_button(self, label):
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(wx.StaticText(self, label=label, size=(80,-1)), 0, wx.ALL, 5)
        add_btn = wx.Button(self, label='Add Row')
        self.Bind(wx.EVT_BUTTON, self.OnAddRow, add_btn)
        sizer.Add(add_btn)
        return sizer

    def OnAddRow(self, event):
        self._editor.add_row()

    def get_value(self):
        return self._editor.get_value()


class _EditorGrid(GridEditor):

    def __init__(self, parent, value):
        GridEditor.__init__(self, parent)
        self._set_default_sizes()
        self._bind_actions()
        self._create_grid(value)
        self._initialize_value(value)

    def _set_default_sizes(self):
        self.SetColLabelSize(0)
        self.SetRowLabelSize(0)
        self.SetDefaultColSize(175)

    def _bind_actions(self):
        accelrators = []
        for mod, key, handler in [
                 (wx.ACCEL_CTRL, ord('c'), self.OnCopy),
                 (wx.ACCEL_CTRL, ord('x'), self.OnCut),
                 (wx.ACCEL_CTRL, ord('v'), self.OnPaste),
                 (wx.ACCEL_CTRL, ord('z'), self.OnUndo),
                 (wx.ACCEL_NORMAL, wx.WXK_DELETE, self.OnDelete)]:
            id = wx.NewId()
            self.Bind(wx.EVT_MENU, handler, id=id)
            accelrators.append((mod, key, id))
        self.SetAcceleratorTable(wx.AcceleratorTable(accelrators))

    def _create_grid(self, value):
        cols = 4
        rows = len(value)/cols + 2
        self.CreateGrid(rows, cols)

    def _initialize_value(self, value):
        for index, item in enumerate(value): 
            row, col = divmod(index, self.NumberCols)
            self.SetCellValue(row, col, item)

    def add_row(self):
        self.AppendRows()

    def get_value(self):
        value = []
        for row in range(self.NumberRows):
            for col in range(self.NumberCols):
                value.append(self.GetCellValue(row, col))
        while not value[-1]:
            value.pop()
        return value

    def OnCopy(self, event):
        self.copy()

    def OnCut(self, event):
        self.cut()

    def OnPaste(self, event):
        self.paste()

    def OnDelete(self, event):
        self.delete()

    def OnUndo(self, event):
        self.undo()

class MultiLineEditor(ValueEditor):
    _sizer_flags_for_editor = wx.ALL|wx.EXPAND

    def _get_text_ctrl(self):
        return wx.TextCtrl(self, style=wx.TE_MULTILINE, size=(600, 400))


class ContentAssistEditor(ValueEditor):

    def _get_text_ctrl(self):
        return ContentAssistTextCtrl(self, self.Parent.datafile, (500, -1))
