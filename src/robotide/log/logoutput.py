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

import wx
from wx import Colour

from .. import widgets
from ..preferences import RideSettings
from wx.stc import StyledTextCtrl


def message_to_string(msg):
    message = msg.replace('\t', '    ')
    return message


class LogOutput(wx.Panel):

    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        self._output = StyledTextCtrl(self, wx.ID_ANY, style=wx.TE_READONLY | wx.TE_MULTILINE | wx.TE_NOHIDESEL)
        self.SetSizer(widgets.VerticalSizer())
        _settings = RideSettings()
        self.run_settings = _settings['Plugins']['Run Anything']
        fore = self.run_settings.get('foreground', '#ffffff')
        backg = self.run_settings.get('background', '#241F31')
        self._output.SetBackgroundColour(Colour(backg))
        self._output.SetForegroundColour(Colour(fore))
        self._output.StyleSetSpec(wx.stc.STC_STYLE_DEFAULT, f"fore:{fore}, back:{backg}")
        self._output.StyleSetBackground(wx.stc.STC_STYLE_DEFAULT, backg)
        self._output.Bind(wx.EVT_KEY_DOWN, self.on_key_down)
        self._output.SetSize(self.Size)
        self.Sizer.add_expanding(self._output)
        self.SetFont(widgets.Font().fixed_log)
        self.Bind(wx.EVT_SIZE, self.on_size)
        self.Layout()
        # print(f"DEBUG: runanything.py LogOutput end init output={self._output}")

    def close(self):
        self._output.Close()

    def update_log(self, log=None):
        if not log:
            return
        if isinstance(log, list):
            content = self._decode_log(log)
        else:
            content = log
        # print(f"DEBUG: runanything.py LogOutput update_log content={content}")
        text_size = len(content)
        self._output.SetReadOnly(False)
        self._output.SetText(content)
        self._output.SetStyling(text_size, wx.stc.STC_STYLE_DEFAULT)
        self._output.SetReadOnly(True)
        self._output.Refresh()

    @staticmethod
    def _decode_log(log):
        result = ''
        for msg in log:
            result += message_to_string(msg)
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

    def SelectAll(self):
        self._output.SetSelection(-1, -1)
