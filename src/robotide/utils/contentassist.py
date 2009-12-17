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
from components import RidePopupWindow


_PREFERRED_POPUP_SIZE = (450, 200)
_PREFERRED_DETAILS_SIZE = (500, 200)


class _ContentAssistTextCtrlBase(object):
    
    def __init__(self, item):
        self._item = item
        self._popup = ContentAssistPopup(self)
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
        
    def show_content_assist(self):
        if self._populate_content_assist():
            self._show_content_assist()
        
    def _populate_content_assist(self, event=None):
        value = self.GetValue()
        if event is not None:
            if event.GetKeyCode() == wx.WXK_BACK:
                value = value[:-1]
            elif event.GetKeyCode() == wx.WXK_ESCAPE:
                self.hide()            
            else:
                value += chr(event.GetRawKeyCode())
        return self._popup.content_assist_for(value, self._item)
                
    def _show_content_assist(self):
        height = self.GetSizeTuple()[1]
        x, y = self.ClientToScreenXY(0, height)
        self._popup.show(x, y)
        
    def content_assist_value(self):
        return self._popup.content_assist_value(self.Value)

    def hide(self):
        self._popup.hide()


class ExpandingContentAssistTextCtrl(_ContentAssistTextCtrlBase, ExpandoTextCtrl):

    def __init__(self, parent, item, size=wx.DefaultSize):
        ExpandoTextCtrl.__init__(self, parent, size=size, style=wx.WANTS_CHARS)
        _ContentAssistTextCtrlBase.__init__(self, item)


class ContentAssistTextCtrl(_ContentAssistTextCtrlBase, wx.TextCtrl):

    def __init__(self, parent, item, size=wx.DefaultSize):
        wx.TextCtrl.__init__(self, parent, size=size, style=wx.WANTS_CHARS)
        _ContentAssistTextCtrlBase.__init__(self, item)


class ContentAssistPopup(object):

    def __init__(self, parent):
        self._parent = parent
        self._main_popup = RidePopupWindow(parent, _PREFERRED_POPUP_SIZE)
        self._details_popup = RidePopupWindow(parent, _PREFERRED_DETAILS_SIZE)
        self._selection = -1
        self._list = ContentAssistList(self._main_popup, self.OnListItemSelected, 
                                       self.OnListItemActivated)
    
    def get_value(self):
        return self._selection != -1 and self._list.get_text(self._selection) or None

    def content_assist_for(self, value, datafile):
        var_index = self._get_variable_start_index(value)
        if  var_index != -1:
            variables = datafile.get_variables()
            self._choices = [ var for var in variables if self._starts(var.name, value[var_index:]) ]
            colnames = 'name', 'value'
            data = [ (var.name, var.parent) for var in self._choices ]
        else:
            keywords = datafile.get_keywords_for_content_assist()
            self._choices = [ kw for kw in keywords if self._starts(kw.name, value) ]
            colnames = 'name', 'source'
            data = [ (kw.name, kw.source) for kw in self._choices ]
        if not self._choices:
            self._list.ClearAll()
            self.hide()
            return False
        self._list.populate(colnames, data)
        return True

    def _get_variable_start_index(self, value):
        return max(value.rfind('$'), value.rfind( '@'))

    def _starts(self, val1, val2):
        return val1.lower().startswith(val2.lower())

    def content_assist_value(self, value):
        if self._selection > -1:
            var_index = self._get_variable_start_index(value)
            if var_index != -1:
                return value[:var_index] + self._list.GetItem(self._selection).GetText()
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
        details = item.get_details()
        if details:
            self._details_popup.Show()
            self._details_popup.set_content(details)


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
            self.InsertStringItem(row, item[0])
            self.SetStringItem(row, 1, item[1])
        self.Select(0)

    def _create_columns(self, colnames):
        for index, colname in enumerate(colnames):
            self.InsertColumn(index, colname)
        self.SetColumnWidth(0, 230)
        self.resizeLastColumn(_PREFERRED_POPUP_SIZE[0]-230)
        
    def get_text(self, index):
        return self.GetItem(index).GetText()
