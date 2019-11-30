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

from robotide.context import POPUP_BACKGROUND, IS_WINDOWS
from robotide.widgets import VerticalSizer, HtmlWindow, HtmlDialog


class _PopupWindowBase(object):

    def __init__(self, size, detachable=True, autohide=False):
        # print("DEBUG: PopupWindow at init")
        self.panel = self._create_ui(size)
        if autohide:
            self._set_auto_hiding()
        if detachable:
            self._set_detachable()
        self.SetSize(size)

    def _create_ui(self, size):
        if wx.VERSION >= (3, 0, 3, ''):  # DEBUG wxPhoenix
            panel = wx.MiniFrame(self)  # DEBUG wx.Panel would not detach on wxPython 4
        else:
            panel = wx.Panel(self)
        panel.SetBackgroundColour(POPUP_BACKGROUND)
        szr = VerticalSizer()
        self._details = HtmlWindow(self, size=size)
        szr.add_expanding(self._details)
        panel.SetSizer(szr)
        panel.Fit()
        return panel

    def _set_detachable(self):
        # print("DEBUG: PopupWindow at Binding mouse on help")
        self._details.Bind(wx.EVT_LEFT_UP, self._detach)
        self._details.Bind(wx.EVT_LEFT_DCLICK, self._detach) # DEBUG add double-click

    def _detach(self, event):
        # print("DEBUG: PopupWindow at detached call")
        self.hide()
        dlg = HtmlDialog(self._detached_title, self._current_details)
        dlg.SetPosition((wx.GetMouseState().x, wx.GetMouseState().y))
        dlg.Show()
        event.Skip()

    def show_at(self, position):
        if self.GetPosition() != position:
            self.SetPosition(position)
        if not self.IsShown():
            self.Show()

    def hide(self, event=None):
        self.Show(False)

    @property
    def screen_position(self):
        return self.ScreenPosition

    @property
    def size(self):
        return self.Size

    def set_content(self, content, title=None):
        color = ''.join(hex(item)[2:] for item in POPUP_BACKGROUND)
        self._current_details = '<body bgcolor=#%s>%s</body>' % \
            (color, content)
        self._details.SetPage(self._current_details)
        self._detached_title = title


class RidePopupWindow(wx.PopupWindow, _PopupWindowBase):

    def __init__(self, parent, size):
        wx.PopupWindow.__init__(self, parent,
                                flags=wx.CAPTION|wx.RESIZE_BORDER|
                                      wx.DEFAULT_FRAME_STYLE)
        self.SetSize(size)

    def _set_auto_hiding(self):
        # EVT_LEAVE is triggered on different components on different OSes.
        component_to_hide = self.panel if IS_WINDOWS else self
        component_to_hide.Bind(wx.EVT_LEAVE_WINDOW, self.hide)


class HtmlPopupWindow(RidePopupWindow):

    def __init__(self, parent, size, detachable=True, autohide=False):
        RidePopupWindow.__init__(self, parent, size)
        _PopupWindowBase.__init__(self, size, detachable, autohide)
        # print("DEBUG: HtmlPopupWindow we must make it border in Windows to be detached")


# TODO: See if we need to have Mac specific window
class MacRidePopupWindow(wx.MiniFrame, _PopupWindowBase):

    def __init__(self, parent, size, detachable=True, autohide=False):
        wx.MiniFrame.__init__(self, parent, style=wx.SIMPLE_BORDER
                                                  |wx.RESIZE_BORDER)
        # set Left to Right direction (while we don't have localization)
        self.SetLayoutDirection(wx.Layout_LeftToRight)
        _PopupWindowBase.__init__(self, size, detachable, autohide)
        self.hide()

    def _set_auto_hiding(self):
        self._details.Bind(wx.EVT_MOTION, lambda evt: self.hide())

    def OnKey(self, *params):
        pass


if wx.PlatformInfo[0] == '__WXMAC__':
    RidePopupWindow = HtmlPopupWindow = MacRidePopupWindow
del MacRidePopupWindow
