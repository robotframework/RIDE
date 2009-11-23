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

from robotide import utils


class ValueEditor(wx.Panel):
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
        self._editor.SelectAll()


class MultiLineEditor(ValueEditor):
    _sizer_flags_for_editor = wx.ALL|wx.EXPAND

    def _get_text_ctrl(self):
        return wx.TextCtrl(self, style=wx.TE_MULTILINE, size=(600, 400))


class ContentAssistEditor(ValueEditor):

    def _get_text_ctrl(self):
        return utils.ContentAssistTextCtrl(self, self.Parent.datafile, (500, -1))
