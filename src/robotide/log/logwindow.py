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

import wx
from wx import Colour

from .. import widgets
from ..widgets import RIDEDialog
from wx.stc import StyledTextCtrl


def message_to_string(msg, parserlog=False):
    message = msg.message.replace('\n\t', '') if parserlog else msg.message
    return '%s [%s]: %s\n\n' % (msg.timestamp, msg.level, message)


class LogWindow(wx.Panel):

    def __init__(self, notebook, title, log):
        wx.Panel.__init__(self, notebook)
        self.dlg = RIDEDialog()
        self.title = title
        self._removetabs = self.title == 'Parser Log'
        self._output = StyledTextCtrl(self, wx.ID_ANY, style=wx.TE_READONLY | wx.TE_MULTILINE | wx.TE_NOHIDESEL)
        fore = self.dlg.color_foreground
        backg = self.dlg.color_background
        self._output.SetBackgroundColour(Colour(backg))
        self._output.SetForegroundColour(Colour(fore))
        self._output.StyleSetSpec(wx.stc.STC_STYLE_DEFAULT, f"fore:{fore}, back:{backg}")
        self._output.StyleSetBackground(wx.stc.STC_STYLE_DEFAULT, backg)
        self._output.Bind(wx.EVT_KEY_DOWN, self.on_key_down)
        self._log = log
        self._add_to_notebook(notebook)
        self.SetFont(widgets.Font().fixed_log)
        self.Bind(wx.EVT_SIZE, self.on_size)

    def _create_ui(self):
        self.SetSizer(widgets.VerticalSizer())
        self.Sizer.add_expanding(self._output)

    def _add_to_notebook(self, notebook):
        notebook.add_tab(self, self.title, allow_closing=True)
        notebook.show_tab(self)
        self._output.SetSize(self.Size)

    def close(self, notebook):
        self._output.Close()
        notebook.delete_tab(self)

    def update_log(self):
        content = self._decode_log(self._log)
        text_size = len(content)
        self._output.SetReadOnly(False)
        self._output.SetText(content)
        self._output.SetStyling(text_size, wx.stc.STC_STYLE_DEFAULT)
        self._output.SetReadOnly(True)
        self._output.Refresh()

    def _decode_log(self, log):
        result = ''
        for msg in log:
            result += message_to_string(msg, self._removetabs)
        return result

    def on_size(self, evt):
        _ = evt
        self._output.SetSize(self.Size)

    def on_key_down(self, event):
        keycode = event.GetKeyCode()

        if event.ControlDown() and keycode == ord('A'):
            self.SelectAll()
        else:
            event.Skip()

    def Copy(self):
        """ Overriden in purpose """
        pass

    def SelectAll(self):
        self._output.SetSelection(-1, -1)
