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

from . import htmlwindow, sizers
from wx import Colour

# TODO: Make this colour configurable
# HTML_BACKGROUND = (240, 242, 80)  # (200, 222, 40)
# _settings = RideSettings()
# general_settings = _settings['General']
# HTML_BACKGROUND = general_settings['background help']
# Workaround for circular import
HTML_BACKGROUND = (240, 242, 80)
HTML_FOREGROUND = (7, 0, 70)
general_settings = {'background help': HTML_BACKGROUND, 'foreground help': HTML_FOREGROUND,
                    'font face': '', 'font size': 11}


class HtmlWindow(html.HtmlWindow):

    def __init__(self, parent, size=wx.DefaultSize, text=None):
        html.HtmlWindow.__init__(self, parent, size=size)
        self.SetBorders(2)
        self.SetStandardFonts(size=9)
        if text:
            self.set_content(text)
        self.SetHTMLBackgroundColour(Colour(general_settings['background help']))
        self.SetForegroundColour(Colour(general_settings['foreground help']))
        self.font = self.GetFont()
        self.font.SetFaceName(general_settings['font face'])
        self.font.SetPointSize(general_settings['font size'])
        self.SetFont(self.font)
        self.Refresh(True)
        self.Bind(wx.EVT_KEY_DOWN, self.OnKeyDown)

    def set_content(self, content):
        color = ''.join(hex(item)[2:] for item in general_settings['background help'])
        _content = '<body bgcolor=#%s>%s</body>' % (color, content)
        self.SetPage(_content)

    def OnKeyDown(self, event):
        if self._is_copy(event):
            self._add_selection_to_clipboard()
        self.Parent.OnKey(event)
        event.Skip()

    @staticmethod
    def _is_copy(event):
        return event.GetKeyCode() == ord('C') and event.CmdDown()

    def _add_selection_to_clipboard(self):
        wx.TheClipboard.Open()
        wx.TheClipboard.SetData(wx.TextDataObject(self.SelectionToText()))
        wx.TheClipboard.Close()

    def OnLinkClicked(self, link):
        webbrowser.open(link.Href)

    def close(self):
        self.Show(False)

    def clear(self):
        self.SetPage('')


class RIDEDialog(wx.Dialog):

    def __init__(self, title='', parent=None, size=None, style=None):
        parent = parent or wx.GetTopLevelWindows()[0]
        size = size or (-1, -1)
        style = style or (wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
        wx.MiniFrame.__init__(self, parent, title=title, size=size, style=style)
        # set Left to Right direction (while we don't have localization)
        self.SetLayoutDirection(wx.Layout_LeftToRight)
        self.SetBackgroundColour(Colour(200, 222, 40))
        self.SetOwnBackgroundColour(Colour(200, 222, 40))
        self.SetForegroundColour(Colour(7, 0, 70))
        self.SetOwnForegroundColour(Colour(7, 0, 70))
        self.CenterOnParent()

    def _create_buttons(self, sizer):
        buttons = self.CreateStdDialogButtonSizer(wx.OK | wx.CANCEL)
        sizer.Add(buttons, flag=wx.ALIGN_CENTER | wx.ALL, border=5)

    def _create_horizontal_line(self, sizer):
        line = wx.StaticLine(self, size=(20, -1), style=wx.LI_HORIZONTAL)
        if wx.VERSION < (4, 1, 0):
            sizer.Add(line, border=5, flag=wx.GROW | wx.ALIGN_CENTER_VERTICAL | wx.RIGHT | wx.TOP)
        else:
            sizer.Add(line, border=5, flag=wx.GROW | wx.RIGHT | wx.TOP)

    def execute(self):
        retval = None
        if self.ShowModal() == wx.ID_OK:
            retval = self._execute()
        self.Destroy()
        return retval

    def _execute(self):
        raise NotImplementedError(self.__class__.__name__)


class HtmlDialog(RIDEDialog):

    def __init__(self, title, content, padding=0, font_size=-1):
        RIDEDialog.__init__(self, title)
        # set Left to Right direction (while we don't have localization)
        self.SetLayoutDirection(wx.Layout_LeftToRight)
        szr = sizers.VerticalSizer()
        html_wnd = HtmlWindow(self, text=content)
        html_wnd.SetStandardFonts(size=font_size)
        html_wnd.SetBackgroundColour(Colour(HTML_BACKGROUND))
        html_wnd.SetForegroundColour(Colour(7, 0, 70))
        szr.add_expanding(html_wnd, padding=padding)
        self.SetSizer(szr)

    def OnKey(self, event):
        pass
