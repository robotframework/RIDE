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

from robotide.widgets import htmlwindow, sizers


class Dialog(wx.Dialog):

    def __init__(self, title='', parent=None, size=None, style=None):
        parent = parent or wx.GetTopLevelWindows()[0]
        size = size or (-1, -1)
        # wx.THICK_FRAME allows resizing
        if wx.VERSION >= (3, 0, 3, ''):  # DEBUG wxPhoenix
            style = style or (wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
            wx.MiniFrame.__init__(self, parent, title=title, size=size, style=style) # style=wx.SIMPLE_BORDER)
        else:
            style = style or (wx.DEFAULT_DIALOG_STYLE | wx.THICK_FRAME)
            wx.Dialog.__init__(self, parent, title=title, size=size, style=style)
        # set Left to Right direction (while we don't have localization)
        self.SetLayoutDirection(wx.Layout_LeftToRight)
        # print(
        #    "DEBUG: Created detached dialog, did it work in Windows?")
        # wx.Dialog.__init__(self, parent, title=title, size=size, style=style)
        self.CenterOnParent()

    def _create_buttons(self, sizer):
        buttons = self.CreateStdDialogButtonSizer(wx.OK | wx.CANCEL)
        sizer.Add(buttons, flag=wx.ALIGN_CENTER | wx.ALL, border=5)

    def _create_horizontal_line(self, sizer):
        line = wx.StaticLine(self, size=(20, -1), style=wx.LI_HORIZONTAL)
        sizer.Add(
            line, border=5,
            flag=wx.GROW | wx.ALIGN_CENTER_VERTICAL | wx.RIGHT | wx.TOP)

    def execute(self):
        retval = None
        if self.ShowModal() == wx.ID_OK:
            retval = self._execute()
        self.Destroy()
        return retval

    def _execute(self):
        raise NotImplementedError(self.__class__.__name__)


class HtmlDialog(Dialog):

    def __init__(self, title, content, padding=0, font_size=-1):
        Dialog.__init__(self, title)
        # set Left to Right direction (while we don't have localization)
        self.SetLayoutDirection(wx.Layout_LeftToRight)
        szr = sizers.VerticalSizer()
        html = htmlwindow.HtmlWindow(self, text=content)
        html.SetStandardFonts(size=font_size)
        szr.add_expanding(html, padding=padding)
        self.SetSizer(szr)

    def OnKey(self, event):
        pass
