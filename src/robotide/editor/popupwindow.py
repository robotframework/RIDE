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

from robotide import context
from robotide.utils import RideHtmlWindow
from robotide.widgets import ButtonWithHandler, Dialog, VerticalSizer


class RidePopupWindow(wx.PopupWindow):

    def __init__(self, parent, size):
        wx.PopupWindow.__init__(self, parent)
        self.SetSize(size)

    def show_at(self, position):
        if not self.IsShown():
            self.SetPosition(position)
            self.Show()

    def hide(self):
        self.Show(False)

    def _detach(self, event):
        HtmlDialog(self._current_details).Show()
        self.hide()


class RideHtmlPopupWindow(RidePopupWindow):

    def __init__(self, parent, size):
        RidePopupWindow.__init__(self, parent, size)
        panel = wx.Panel(self)
        panel.SetBackgroundColour(context.POPUP_BACKGROUND)
        szr = VerticalSizer()
        btn = ButtonWithHandler(panel, 'Detach', width=size[0],
                                handler=self._detach)
        self._details = RideHtmlWindow(self, size=(size[0], size[1]-25))
        szr.add_expanding(self._details)
        szr.add(btn)
        panel.SetSizer(szr)
        panel.Fit()

    def set_content(self, content):
        color = ''.join(hex(item)[2:] for item in context.POPUP_BACKGROUND)
        self._current_details = '<body bgcolor=#%s>%s</body>' % (color, content)
        self._details.SetPage(self._current_details)


class RideToolTipWindow(RideHtmlPopupWindow):

    def __init__(self, parent, size):
        RideHtmlPopupWindow.__init__(self, parent, size)
        self.Bind(wx.EVT_LEAVE_WINDOW, self.OnLeaveWindow)

    def OnLeaveWindow(self, event):
        self.hide()


class MacRidePopupWindow(wx.Window):
    """Mac version of RidePopupWindow with very limited functionality.

    wx.PopupWindow does not work on Mac and without this hack RIDE could
    not be used on that platform at all.
    """

    def __init__(self, parent, size):
        wx.Window.__init__(self, parent)

    set_content = show_at = hide = lambda *args: None

    def IsShown(self):
        return False


class HtmlDialog(Dialog):

    def __init__(self, content):
        Dialog.__init__(self, '')
        szr = VerticalSizer()
        szr.add(RideHtmlWindow(self, text=content, size=self.Size))
        self.SetSizer(szr)

    def OnKey(self, event):
        pass


if wx.PlatformInfo[0] == '__WXMAC__':
    RidePopupWindow = RideToolTipWindow = RideHtmlPopupWindow = MacRidePopupWindow
del MacRidePopupWindow
