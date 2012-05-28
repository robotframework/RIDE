#  Copyright 2008-2012 Nokia Siemens Networks Oyj
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
from robotide import utils
from robotide.widgets import (ButtonWithHandler, Dialog, VerticalSizer,
        HtmlWindow)


class RidePopupWindow(wx.PopupWindow):

    def __init__(self, parent, size):
        wx.PopupWindow.__init__(self, parent)
        self.SetSize(size)

    def show_at(self, position):
        if not self.IsShown():
            self.SetPosition(position)
            self.Show()

    def hide(self, event=None):
        self.Show(False)

    @property
    def screen_position(self):
        return self.ScreenPosition

    @property
    def size(self):
        return self.Size


class Tooltip(RidePopupWindow):

    def __init__(self, parent, size, detachable=True, autohide=False):
        RidePopupWindow.__init__(self, parent, size)
        self._create_ui(size, detachable, autohide)

    def _create_ui(self, size, detachable, autohide):
        panel = wx.Panel(self)
        panel.SetBackgroundColour(POPUP_BACKGROUND)
        szr = VerticalSizer()
        self._details = HtmlWindow(self, size=size)
        if detachable:
            self._details.Bind(wx.EVT_LEFT_UP, self._detach)
        szr.add_expanding(self._details)
        panel.SetSizer(szr)
        panel.Fit()
        if autohide:
            self._get_autohide_component(panel).Bind(wx.EVT_LEAVE_WINDOW,
                                                     self.hide)

    def _get_autohide_component(self, panel):
        return panel if IS_WINDOWS else self

    def set_content(self, content, title=None, html=True):
        color = ''.join(hex(item)[2:] for item in POPUP_BACKGROUND)
        if not html:
            content = utils.html_format(content)
        self._current_details = '<body bgcolor=#%s>%s</body>' % (color, content)
        self._details.SetPage(self._current_details)
        self._detached_title = title

    def _detach(self, event):
        self.hide()
        dlg = HtmlDialog(self._detached_title, self._current_details)
        dlg.SetPosition((wx.GetMouseState().x, wx.GetMouseState().y))
        dlg.Show()
        event.Skip()


class MacRidePopupWindow(wx.Frame):
    """This class in now an exact copy of RidePopupWindow except that it takes
    wx.Frame instead of wx.PopupWindow and that it has a style of wx.SIMPLE_BORDER.
    This violates the DRY principal but
    I'm not skilled enough in python yet to know how to fix it.  Someone who
    knows better should feel free to encapsulate this
    """

    def __init__(self, parent, size, detachable=True, autohide=False):
        wx.Frame.__init__(self, parent, style=wx.SIMPLE_BORDER)
        self.SetSize(size)
        self._create_ui(size, detachable, autohide)
        self.hide()

    def show_at(self, position):
        if not self.IsShown():
            self.SetPosition(position)
            self.Show()

    def hide(self, event=None):
        self.Show(False)

    @property
    def screen_position(self):
        return self.ScreenPosition

    @property
    def size(self):
        return self.Size

    def _create_ui(self, size, detachable, autohide):
        panel = wx.Panel(self)
        panel.SetBackgroundColour(POPUP_BACKGROUND)
        szr = VerticalSizer()
        self._details = HtmlWindow(self, size=size)
        if detachable:
            self._details.Bind(wx.EVT_LEFT_UP, self._detach)
        szr.add_expanding(self._details)
        panel.SetSizer(szr)
        panel.Fit()
        if autohide:
            self._details.Bind(wx.EVT_MOTION, self.OnMouseMotion)
            self._get_autohide_component(panel).Bind(wx.EVT_LEAVE_WINDOW,
                                                     self.hide)

    def OnMouseMotion(self, evt):
        self.hide()

    def _get_autohide_component(self, panel):
        return self

    def set_content(self, content, title=None, html=True):
        color = ''.join(hex(item)[2:] for item in POPUP_BACKGROUND)
        if not html:
            content = utils.html_format(content)
        self._details.SetPage('<body bgcolor=#%s><center>%s</center></body>'
                              % (color, content))
        self._detached_title = title

    def _detach(self, event):
        self.hide()
        dlg = HtmlDialog(self._detached_title, self._details.ToText())
        dlg.SetPosition((wx.GetMouseState().x, wx.GetMouseState().y))
        dlg.Show()

    def OnKey(self, *params):
        pass


class HtmlDialog(Dialog):

    def __init__(self, title, content):
        Dialog.__init__(self, title)
        szr = VerticalSizer()
        szr.add_expanding(HtmlWindow(self, text=content, size=self.Size))
        self.SetSizer(szr)

    def OnKey(self, event):
        pass


if wx.PlatformInfo[0] == '__WXMAC__':
    RidePopupWindow = Tooltip = MacRidePopupWindow
del MacRidePopupWindow
