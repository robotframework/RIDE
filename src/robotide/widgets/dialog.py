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

from . import sizers, ButtonWithHandler


class HtmlWindow(html.HtmlWindow):

    def __init__(self, parent, size=wx.DefaultSize, text=None, color_background=None, color_foreground=None):
        html.HtmlWindow.__init__(self, parent, size=size, style=html.HW_DEFAULT_STYLE)
        from ..preferences import RideSettings
        _settings = RideSettings()
        self.general_settings = _settings['General']
        self.color_background_help = color_background if color_background else self.general_settings['background help']
        self.color_foreground_text = color_foreground if color_foreground else self.general_settings['foreground text']
        self.SetBorders(2)
        self.SetStandardFonts(size=9)
        if text:
            self.set_content(text)
        self.font = self.GetFont()
        self.font.SetFaceName(self.general_settings['font face'])
        self.font.SetPointSize(self.general_settings['font size'])
        self.SetFont(self.font)
        self.Refresh(True)
        self.Bind(wx.EVT_KEY_DOWN, self.on_key_down)
        self.Bind(wx.EVT_CLOSE, self.close)

    def set_content(self, content):
        if isinstance(self.color_background_help, tuple):
            bgcolor = '#' + ''.join(hex(item)[2:] for item in self.color_background_help)
        else:
            bgcolor = self.color_background_help
        if isinstance(self.color_foreground_text, tuple):
            fgcolor = '#' + ''.join(hex(item)[2:] for item in self.color_foreground_text)
        else:
            fgcolor = self.color_foreground_text
        if content.startswith('<table>'):
            new_content = content.replace("<table>", f'<div><font color="{fgcolor}"><table>')\
                .replace("</table>", "</table></font></div>")
        else:
            new_content = f'<p><font color="{fgcolor}">' + content + '</font></p>'
        _content = '<body bgcolor=%s style="color:%s;">%s</body>' % (bgcolor, fgcolor, new_content)
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
        self.Destroy()

    def clear(self):
        self.SetPage('')


class RIDEDialog(wx.Dialog):

    def __init__(self, title='', parent=None, size=None, style=None, message=None):
        size = size or (-1, -1)
        style = style or (wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
        wx.Dialog.__init__(self, parent=parent, title=title, size=size, style=style)
        # set Left to Right direction (while we don't have localization)
        self.SetLayoutDirection(wx.Layout_LeftToRight)
        self.message = message
        from ..preferences import RideSettings
        _settings = RideSettings()
        self.general_settings = _settings['General']
        self.font_face = self.general_settings['font face']
        self.font_size = self.general_settings['font size']
        self.color_background = self.general_settings['background']
        self.color_foreground = self.general_settings['foreground']
        self.color_secondary_background = self.general_settings['secondary background']
        self.color_secondary_foreground = self.general_settings['secondary foreground']
        self.color_background_help = self.general_settings['background help']
        self.color_foreground_text = self.general_settings['foreground text']
        self.SetBackgroundColour(Colour(self.color_background))
        self.SetForegroundColour(Colour(self.color_foreground))
        if self.message:
            sizer = wx.BoxSizer(wx.VERTICAL)
            content = wx.StaticText(self, -1, self.message)
            button = wx.Button(self, wx.ID_OK, '', style=style)
            content.SetBackgroundColour(Colour(self.color_background))
            content.SetForegroundColour(Colour(self.color_foreground))
            button.SetBackgroundColour(Colour(self.color_secondary_background))
            button.SetForegroundColour(Colour(self.color_secondary_foreground))
            sizer.Add(content, 0, wx.ALL | wx.EXPAND, 3)
            sizer.Add(wx.StaticText(self, -1, "\n\n"), 0, wx.ALL, 3)
            sizer.Add(button, 0, wx.ALIGN_CENTER | wx.BOTTOM, 5)
            self.SetSizer(sizer)
            sizer.Fit(self)
        self.CenterOnParent()

    def _create_buttons(self, sizer):
        buttons = self.CreateStdDialogButtonSizer(wx.OK | wx.CANCEL)
        self.SetBackgroundColour(Colour(self.color_background))
        self.SetForegroundColour(Colour(self.color_foreground))
        for item in self.GetChildren():
            if isinstance(item, (wx.Button, wx.BitmapButton, ButtonWithHandler)):
                item.SetBackgroundColour(Colour(self.color_secondary_background))
                # item.SetOwnBackgroundColour(Colour(self.color_secondary_background))
                item.SetForegroundColour(Colour(self.color_secondary_foreground))
                # item.SetOwnForegroundColour(Colour(self.color_secondary_foreground))
        sizer.Add(buttons, flag=wx.ALIGN_CENTER | wx.ALL, border=5)
        sizer.Fit(self)

    def _create_horizontal_line(self, sizer):
        line = wx.StaticLine(self, size=(20, -1), style=wx.LI_HORIZONTAL)
        if wx.VERSION < (4, 1, 0):
            sizer.Add(line, border=5, flag=wx.GROW | wx.ALIGN_CENTER_VERTICAL | wx.RIGHT | wx.TOP)
        else:
            sizer.Add(line, border=5, flag=wx.GROW | wx.RIGHT | wx.TOP)
        sizer.Fit(self)

    def execute(self):
        retval = None
        if self.ShowModal() == wx.ID_OK:
            retval = self._execute()
        self.Destroy()
        return retval

    def _execute(self):
        raise NotImplementedError(self.__class__.__name__)


class HtmlDialog(RIDEDialog):

    def _execute(self):
        """ Nothing to execute in this dialog """
        pass

    def __init__(self, title, content, padding=0, font_size=-1):
        RIDEDialog.__init__(self, title)
        # set Left to Right direction (while we don't have localization)
        self.SetLayoutDirection(wx.Layout_LeftToRight)
        szr = sizers.VerticalSizer()
        self.SetMinClientSize((200, 300))
        self.html_wnd = HtmlWindow(self, text=content)
        self.html_wnd.SetStandardFonts(size=font_size)
        szr.add_expanding(self.html_wnd, padding=padding)
        self.SetSizer(szr)
        szr.Fit(self)
        self.Layout()

    def on_key(self, event):
        """ In the event we need to process key events"""
        pass
