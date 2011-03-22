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
from robotide import utils
from robotide.widgets import ButtonWithHandler, Dialog, VerticalSizer


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


class Tooltip(RidePopupWindow):

    def __init__(self, parent, size, detachable=True, autohide=False):
        RidePopupWindow.__init__(self, parent, size)
        self._create_ui(size, detachable, autohide)

    def _create_ui(self, size, detachable, autohide):
        panel = wx.Panel(self)
        panel.SetBackgroundColour(context.POPUP_BACKGROUND)
        szr = VerticalSizer()
        if detachable:
            szr.add(ButtonWithHandler(panel, 'Detach', width=size[0],
                                      handler=self._detach))
            size = (size[0], size[1]-25)
        self._details = RideHtmlWindow(self, size=size)
        szr.add_expanding(self._details)
        panel.SetSizer(szr)
        panel.Fit()
        if autohide:
            self._get_autohide_component(panel).Bind(wx.EVT_LEAVE_WINDOW,
                                                     self.hide)

    def _get_autohide_component(self, panel):
        return panel if context.is_windows else self

    def set_content(self, content, title=None, html=True):
        color = ''.join(hex(item)[2:] for item in context.POPUP_BACKGROUND)
        if not html:
            content = utils.html_escape(content, formatting=True)
        self._current_details = '<body bgcolor=#%s>%s</body>' % (color, content)
        self._details.SetPage(self._current_details)
        self._detached_title = title

    def _detach(self, event):
        self.hide()
        dlg = HtmlDialog(self._detached_title, self._current_details)
        dlg.SetPosition((wx.GetMouseState().x, wx.GetMouseState().y))
        dlg.Show()


class MacRidePopupWindow(wx.Window):
    """Mac version of RidePopupWindow with very limited functionality.

    wx.PopupWindow does not work on Mac and without this hack RIDE could
    not be used on that platform at all.
    """

    def __init__(self, parent, size, detachable=True, autohide=False):
        wx.Window.__init__(self, parent)

    set_content = show_at = hide = lambda *args: None

    def IsShown(self):
        return False


class HtmlDialog(Dialog):

    def __init__(self, title, content):
        Dialog.__init__(self, title)
        szr = VerticalSizer()
        szr.add_expanding(RideHtmlWindow(self, text=content,
                                         size=self.Size))
        self.SetSizer(szr)

    def OnKey(self, event):
        pass


if wx.PlatformInfo[0] == '__WXMAC__':
    RidePopupWindow = Tooltip = MacRidePopupWindow
del MacRidePopupWindow
