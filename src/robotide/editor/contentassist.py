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
from wx.lib.mixins.listctrl import ListCtrlAutoWidthMixin
from wx.lib.expando import ExpandoTextCtrl

from robotide import context

from popupwindow import RidePopupWindow


_PREFERRED_POPUP_SIZE = (450, 200)
_PREFERRED_DETAILS_SIZE = (500, 200)


class _ContentAssistTextCtrlBase(object):

    def __init__(self, plugin):
        self._popup = ContentAssistPopup(self, plugin)
        self.Bind(wx.EVT_KEY_DOWN, self.OnKey)
        self.Bind(wx.EVT_KILL_FOCUS, self.OnFocusLost)
        self.Bind(wx.EVT_MOVE, self.OnFocusLost)

    def OnKey(self, event):
        keycode = event.GetKeyCode()
        # Ctrl-Space handling needed for dialogs
        if keycode == wx.WXK_SPACE and event.ControlDown():
            self.show_content_assist()
        elif keycode in [wx.WXK_UP, wx.WXK_DOWN, wx.WXK_PAGEUP, wx.WXK_PAGEDOWN] \
                and self._popup.is_shown():
            self._popup.select_and_scroll(keycode)
        elif keycode == wx.WXK_RETURN and self._popup.is_shown():
            self.OnFocusLost(event)
            return
        elif keycode == wx.WXK_TAB:
            self.OnFocusLost(event, False)
        elif keycode == wx.WXK_ESCAPE and self._popup.is_shown():
            self._popup.hide()
            return
        elif self._popup.is_shown() and keycode < 256:
            self._populate_content_assist(event)
        event.Skip()

    def OnFocusLost(self, event, set_value=True):
        if not self._popup.is_shown():
            return
        value = self._popup.get_value()
        if set_value and value:
            self.SetValue(value)
            self.SetInsertionPoint(len(self.Value))
        else:
            self.Clear()
        self.hide()

    def reset(self):
        self._popup.reset()

    def show_content_assist(self):
        if self._populate_content_assist():
            self._show_content_assist()

    def _populate_content_assist(self, event=None):
        value = self.GetValue()
        if event is not None:
            if event.GetKeyCode() == wx.WXK_BACK:
                value = value[:-1]
            elif event.GetKeyCode() == wx.WXK_DELETE:
                pos = self.GetInsertionPoint()
                value = value[:pos] + value[pos+1:]
            elif event.GetKeyCode() == wx.WXK_ESCAPE:
                self.hide()
            else:
                value += chr(event.GetRawKeyCode())
        return self._popup.content_assist_for(value)

    def _show_content_assist(self):
        height = self.GetSizeTuple()[1]
        x, y = self.ClientToScreenXY(0, height)
        self._popup.show(x, y)

    def content_assist_value(self):
        return self._popup.content_assist_value(self.Value)

    def hide(self):
        self._popup.hide()


class ExpandingContentAssistTextCtrl(_ContentAssistTextCtrlBase, ExpandoTextCtrl):

    def __init__(self, parent, plugin, size=wx.DefaultSize):
        ExpandoTextCtrl.__init__(self, parent, size=size, style=wx.WANTS_CHARS)
        _ContentAssistTextCtrlBase.__init__(self, plugin)


class ContentAssistTextCtrl(_ContentAssistTextCtrlBase, wx.TextCtrl):

    def __init__(self, parent, plugin, size=wx.DefaultSize):
        wx.TextCtrl.__init__(self, parent, size=size, style=wx.WANTS_CHARS)
        _ContentAssistTextCtrlBase.__init__(self, plugin)


class ContentAssistPopup(object):

    def __init__(self, parent, plugin):
        self._parent = parent
        self._plugin = plugin
        self._main_popup = RidePopupWindow(parent, _PREFERRED_POPUP_SIZE)
        self._details_popup = RidePopupWindow(parent, _PREFERRED_DETAILS_SIZE)
        self._selection = -1
        self._list = ContentAssistList(self._main_popup, self.OnListItemSelected,
                                       self.OnListItemActivated)

    def reset(self):
        self._selection = -1

    def get_value(self):
        return self._selection != -1 and self._list.get_text(self._selection) or None

    def content_assist_for(self, value):
        self._choices = self._plugin.content_assist_values(value)
        if not self._choices:
            self._list.ClearAll()
            self.hide()
            return False
        self._list.populate(['name', 'source'], self._choices)
        return True

    def _starts(self, val1, val2):
        return val1.lower().startswith(val2.lower())

    def content_assist_value(self, value):
        if self._selection > -1:
            return self._list.GetItem(self._selection).GetText()
        return None

    def show(self, xcoord, ycoord):
        self._main_popup.SetPosition((xcoord, ycoord))
        self._details_popup.SetPosition((xcoord+450, ycoord))
        self._main_popup.Show()
        self._list.SetFocus()

    def is_shown(self):
        return self._main_popup.IsShown()

    def select_and_scroll(self, keycode):
        sel = self._list.GetFirstSelected()
        if keycode == wx.WXK_DOWN :
            if sel < (self._list.GetItemCount()-1):
                self._select_and_scroll(sel+1)
            else:
                self._select_and_scroll(0)
        elif keycode == wx.WXK_UP:
            if sel > 0 :
                self._select_and_scroll(sel-1)
            else:
                self._select_and_scroll(self._list.GetItemCount()-1)
        elif keycode == wx.WXK_PAGEDOWN:
            if self._list.ItemCount-self._selection > 14:
                self._select_and_scroll(self._selection+14)
            else:
                self._select_and_scroll(self._list.ItemCount-1)
        elif keycode == wx.WXK_PAGEUP:
            if self._selection > 14:
                self._select_and_scroll(self._selection-14)
            else:
                self._select_and_scroll(0)

    def _select_and_scroll(self, selection):
        self._selection = selection
        self._list.Select(self._selection)
        self._list.EnsureVisible(self._selection)

    def hide(self):
        self._selection = -1
        self._main_popup.Show(False)
        self._details_popup.Show(False)

    def OnListItemActivated(self, event):
        # TODO: should this be implemented with callback?
        self._parent.OnFocusLost(event)

    def OnListItemSelected(self, event):
        self._selection = event.GetIndex()
        item = self._choices[self._selection]
        if item.details:
            self._details_popup.Show()
            self._details_popup.set_content(item.details)
        elif self._details_popup.IsShown():
            self._details_popup.Show(False)


class ContentAssistList(wx.ListCtrl, ListCtrlAutoWidthMixin):

    def __init__(self, parent, selection_callback, activation_callback=None):
        style = wx.LC_REPORT | wx.LC_SINGLE_SEL | wx.LC_NO_HEADER
        wx.ListCtrl.__init__(self, parent, style=style)
        ListCtrlAutoWidthMixin.__init__(self)
        self._selection_callback = selection_callback
        self._activation_callback = activation_callback
        self.SetSize(parent.GetSize())
        self.SetBackgroundColour(context.POPUP_BACKGROUND)
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, selection_callback)
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, activation_callback)

    def populate(self, colnames, data):
        self.ClearAll()
        self._create_columns(colnames)
        for row, item in enumerate(data):
            self.InsertStringItem(row, item.name)
            self.SetStringItem(row, 1, item.source)
        self.Select(0)

    def _create_columns(self, colnames):
        for index, colname in enumerate(colnames):
            self.InsertColumn(index, colname)
        self.SetColumnWidth(0, 230)
        self.resizeLastColumn(_PREFERRED_POPUP_SIZE[0]-230)

    def get_text(self, index):
        return self.GetItem(index).GetText()
