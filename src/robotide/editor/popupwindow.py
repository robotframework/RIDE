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


class RidePopupWindow(wx.PopupWindow):

    def __init__(self, parent, size):
        wx.PopupWindow.__init__(self, parent)
        self.SetSize(size)
        self._details = RideHtmlWindow(self, size=size)

    def set_content(self, content):
        color = ''.join([hex(item)[2:] for item in context.POPUP_BACKGROUND])
        details = '<body bgcolor=#%s>%s</body>' % (color, content)
        self._details.SetPage(details)

    def show_at(self, position):
        if not self.IsShown():
            self.SetPosition(position)
            self.Show()

    def hide(self):
        self.Show(False)

    def OnLeftUp(self, event):
        self.Parent.OnLeftUp(event)

    def OnLeftDouble(self, event):
        self.Parent.OnLeftDouble(event)


class RideToolTipWindow(RidePopupWindow):

    def __init__(self, parent, size):
        RidePopupWindow.__init__(self, parent, size)
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


if wx.PlatformInfo[0] == '__WXMAC__':
    RidePopupWindow = RideToolTipWindow = MacRidePopupWindow
del MacRidePopupWindow
