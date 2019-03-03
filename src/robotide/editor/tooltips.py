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
import wx.grid

from .popupwindow import HtmlPopupWindow


class GridToolTips(object):

    def __init__(self, grid):
        self._tooltip = HtmlPopupWindow(grid, (250, 80), False, True)
        self._information_popup = HtmlPopupWindow(grid, (450, 300))
        self._grid = grid
        self._tooltip_timer = wx.Timer(grid.GetGridWindow())
        grid.GetGridWindow().Bind(wx.EVT_WINDOW_DESTROY, self.OnGridDestroy)
        grid.GetGridWindow().Bind(wx.EVT_KILL_FOCUS, self.OnGridFocusLost)
        grid.GetGridWindow().Bind(wx.EVT_MOTION, self.OnMouseMotion)
        grid.GetGridWindow().Bind(wx.EVT_TIMER, self.OnShowToolTip)
        grid.Bind(wx.grid.EVT_GRID_EDITOR_HIDDEN, self.OnGridEditorHidden)

    def OnGridDestroy(self, event):
        self._tooltip_timer.Stop()
        event.Skip()

    def OnGridFocusLost(self, event):
        self._tooltip_timer.Stop()
        event.Skip()

    def OnMouseMotion(self, event):
        self._hide_tooltip()
        if event.CmdDown():
            self._tooltip_timer.Stop()
            self._grid.show_cell_information()
        else:
            self._information_popup.hide()
            self._start_tooltip_timer()
        event.Skip()

    def _start_tooltip_timer(self):
        self._tooltip_timer.Start(1000, True)

    def OnShowToolTip(self, event):
        self._hide_tooltip()
        content = self._grid.get_tooltip_content()
        if content and self._application_has_focus():
            self._show_tooltip_at(content, self._calculate_tooltip_position())
            self._grid.SetFocus()

    def _application_has_focus(self):
        window = wx.Window.FindFocus()
        if window is None:
            return False
        rect = window.GetTopLevelParent().GetScreenRect()
        if wx.VERSION >= (3, 0, 3, ''):  # DEBUG wxPhoenix
            return rect.Contains(wx.GetMousePosition())
        else:
            return rect.Inside(wx.GetMousePosition())

    def OnGridEditorHidden(self, event):
        cell = event.Row, event.Col
        if cell == self._grid.cell_under_cursor:
            self._start_tooltip_timer()

    def _show_tooltip_at(self, content, position):
        if not self._information_popup.IsShown():
            self._tooltip.set_content(content)
            self._tooltip.show_at(position)

    def _calculate_tooltip_position(self):
        x, y = wx.GetMousePosition()
        return x + 16, y + 16   # don't place tooltip under cursor

    def _hide_tooltip(self):
        self._tooltip.hide()

    def hide_information(self):
        self._information_popup.hide()

    def hide(self):
        self._hide_tooltip()
        self.hide_information()

    def show_info_at(self, info, title, position):
        self._tooltip.hide()
        self._information_popup.set_content(info, title)
        self._information_popup.show_at(position)
