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
from ..context import POPUP_BACKGROUND, POPUP_FOREGROUND, IS_WINDOWS, IS_MAC
from ..widgets import VerticalSizer, HtmlWindow, HtmlDialog


class _PopupWindowBase(wx.Frame):

    def __init__(self, size, detachable=True, autohide=False, color_background=POPUP_BACKGROUND,
                 color_foreground=POPUP_FOREGROUND):
        self._current_details = None
        self._details = None
        self._detached_title = None
        self.color_background = color_background
        self.color_foreground = color_foreground
        self.panel = self._create_ui(size)
        if autohide:
            self._set_auto_hiding()
        if detachable:
            self._set_detachable()
        self.SetSize(size)

    def _create_ui(self, size):
        panel = wx.MiniFrame(self)
        # DEBUG: Make this colour dependent on colours cycle or by Library
        panel.SetBackgroundColour(self.color_background)
        panel.SetForegroundColour(self.color_foreground)
        szr = VerticalSizer()
        self._details = HtmlWindow(self, size=size)
        szr.add_expanding(self._details)
        # DEBUG: Grid Editor was broken on wxPython 4.2.0 with the SetSizer
        # panel.SetSizerAndFit(szr)
        return panel

    def _set_detachable(self):
        self._details.Bind(wx.EVT_LEFT_UP, self._detach)
        self._details.Bind(wx.EVT_LEFT_DCLICK, self._detach)  # DEBUG add double-click

    def _detach(self, event):
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
        __ = event
        self.Show(False)

    @property
    def screen_position(self):
        return self.ScreenPosition

    @property
    def pw_size(self):
        return self.Size

    def set_content(self, content, title=None):
        if isinstance(self.color_background, tuple):
            bgcolor = '#' + ''.join(hex(item)[2:] for item in self.color_background)
        else:
            bgcolor = self.color_background
        if isinstance(self.color_foreground, tuple):
            fgcolor = '#' + ''.join(hex(item)[2:] for item in self.color_foreground)
        else:
            fgcolor = self.color_foreground
        if content.startswith('<table>'):
            new_content = content.replace("<table>", f'<div><font color="{fgcolor}"><table>')\
                .replace("</table>", "</table></font></div>")
        else:
            new_content = f'<p><font color="{fgcolor}">' + content + '</font></p>'
        self._current_details = '<body bgcolor=%s style="color:%s;">%s</body>' % (bgcolor, fgcolor, new_content)
        self._details.SetPage(self._current_details)
        self._detached_title = title

    def _set_auto_hiding(self):
        raise NotImplementedError


class RidePopupWindow(wx.PopupWindow, _PopupWindowBase):

    def __init__(self, parent, size):
        wx.PopupWindow.__init__(self, parent, flags=wx.CAPTION | wx.RESIZE_BORDER | wx.DEFAULT_FRAME_STYLE)
        self.SetSize(size)

    def _set_auto_hiding(self):
        # EVT_LEAVE is triggered on different components on different OSes.
        component_to_hide = self.panel if IS_WINDOWS else self
        component_to_hide.Bind(wx.EVT_LEAVE_WINDOW, self.hide)


class HtmlPopupWindow(RidePopupWindow):

    def __init__(self, parent, size, detachable=True, autohide=False):
        from ..preferences import RideSettings
        _settings = RideSettings()
        self.general_settings = _settings['General']
        self.color_background_help = self.general_settings['background help']
        self.color_foreground_text = self.general_settings['foreground text']
        RidePopupWindow.__init__(self, parent, size)
        _PopupWindowBase.__init__(self, size, detachable, autohide, color_background=self.color_background_help,
                                  color_foreground=self.color_foreground_text)


# DEBUG: See if we need to have Mac specific window
class MacRidePopupWindow(wx.MiniFrame, _PopupWindowBase):

    def __init__(self, parent, size, detachable=True, autohide=False):
        wx.MiniFrame.__init__(self, parent, style=wx.SIMPLE_BORDER | wx.RESIZE_BORDER)
        # set Left to Right direction (while we don't have localization)
        self.SetLayoutDirection(wx.Layout_LeftToRight)
        from ..preferences import RideSettings
        _settings = RideSettings()
        self.general_settings = _settings['General']
        self.color_background_help = self.general_settings['background help']
        self.color_foreground_text = self.general_settings['foreground text']
        _PopupWindowBase.__init__(self, size, detachable, autohide, color_background=self.color_background_help,
                                  color_foreground=self.color_foreground_text)
        self.hide()

    def _set_auto_hiding(self):
        self._details.Bind(wx.EVT_MOTION, lambda evt: self.hide())

    def on_key(self, *params):
        """ In the event we need to process key events"""
        pass


if IS_MAC:
    RidePopupWindow = HtmlPopupWindow = MacRidePopupWindow
del MacRidePopupWindow
