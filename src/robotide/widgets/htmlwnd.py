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

import webbrowser

import wx
from wx import html, Colour

from ..preferences.settings import RideSettings


_settings = RideSettings()
general_settings = _settings['General']
BACKGROUND_HELP = 'background help'
HTML_BACKGROUND = general_settings[BACKGROUND_HELP]


class HtmlWindow(html.HtmlWindow):

    def __init__(self, parent, size=wx.DefaultSize, text=None):
        html.HtmlWindow.__init__(self, parent, size=size)
        self.SetBorders(2)
        self.SetStandardFonts(size=9)
        self.SetBackgroundColour(Colour(200, 222, 40))
        if text:
            self.set_content(text)
        self.SetHTMLBackgroundColour(Colour(general_settings[BACKGROUND_HELP]))
        self.SetForegroundColour(Colour(general_settings['foreground help']))
        self.font = self.GetFont()
        self.font.SetFaceName(general_settings['font face'])
        self.font.SetPointSize(general_settings['font size'])
        self.SetFont(self.font)
        self.Refresh(True)
        self.Bind(wx.EVT_KEY_DOWN, self.on_key_down)

    def set_content(self, content):
        color = ''.join(hex(item)[2:] for item in general_settings['background help'])
        _content = '<body bgcolor=#%s>%s</body>' % (color, content)
        self.SetPage(_content)

    def on_key_down(self, event):
        if self._is_copy(event):
            self._add_selection_to_clipboard()
        self.Parent.on_key(event)
        event.Skip()

    @staticmethod
    def _is_copy(event):
        return event.GetKeyCode() == ord('C') and event.CmdDown()

    def _add_selection_to_clipboard(self):
        wx.TheClipboard.Open()
        wx.TheClipboard.SetData(wx.TextDataObject(self.SelectionToText()))
        wx.TheClipboard.Close()

    def OnLinkClicked(self, link):  # Overrides wx method
        webbrowser.open(link.Href)

    def close(self):
        self.Show(False)

    def clear(self):
        self.SetPage('')
