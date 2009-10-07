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

from robotide import utils


class ListEditor(wx.Panel):
    _menu = ['Edit', 'Move Up', 'Move Down', '---', 'Delete']
    _buttons = []
    
    def __init__(self, parent, columns, data=[]):
        wx.Panel.__init__(self, parent)
        self._data = data
        self._list = AutoWidthColumnList(self, columns, data)
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnItemSelected)
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnEdit)
        self.Bind(wx.EVT_LIST_ITEM_RIGHT_CLICK, self.OnRightClick)
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self._list, 1, wx.EXPAND)
        sizer.Add((5,0))
        sizer.Add(self._create_buttons())
        sizer.Add((5,0))
        self.SetSizer(sizer)
        sizer.Layout()
        self._selection = -1
        self._columns = columns
        
    def _create_buttons(self):  
        sizer = wx.BoxSizer(wx.VERTICAL)
        for label in self._buttons:
            handler = getattr(self, 'On'+label.replace(' ', ''))
            sizer.Add(utils.create_button(self, label, handler, width=120),
                      0, wx.ALL, 1)
        return sizer

    def OnRightClick(self, event):
        utils.PopupMenu(self, self._menu)
        
    def OnItemSelected(self, event):
        self._selection = event.GetIndex()
        
    def OnItemActivated(self, event):
        pass
            
    def OnMoveUp(self, event):        
        if self._selection < 1:
            return
        self._switch_items(self._selection, self._selection-1)
        self._list.Select(self._selection-1, True)

    def OnMoveDown(self, event):
        if self._selection == self._list.GetItemCount() - 1 or self._selection == -1:
            return
        self._switch_items(self._selection+1, self._selection)
        self._list.Select(self._selection+1, True)

    def _switch_items(self, ind1, ind2):
        self._data.swap(ind1, ind2)
        self.update_data()
        
    def OnDelete(self, event):
        if self._selection == -1:
            return
        self._data.pop(self._selection)
        self.update_data()
        if self._selection >= len(self._data):
            self._selection = len(self._data) - 1
        self._list.Select(self._selection, True)
        
    def update_data(self):
        self._list.DeleteAllItems()
        self._list.insert_data(self._data)
        self.set_dirty()
        
    def update_selected_item(self, data):
        self._list.update_item(self._selection, data)
    
    def set_dirty(self):
        if not self._data.datafile.dirty:
            self._data.datafile.set_dirty()
            self.GetParent().tree.set_dirty(self._data.datafile)
    
    def _check_modified_time(self, event_name):
        if self._data.datafile.has_been_modified_on_disk():
            return self._show_modified_on_disk()
        return True


class AutoWidthColumnList(wx.ListCtrl, ListCtrlAutoWidthMixin):

    def __init__(self, parent, columns, data=[]):
        wx.ListCtrl.__init__(self, parent, 
                             style=wx.LC_REPORT|wx.NO_BORDER|wx.LC_SINGLE_SEL|wx.LC_HRULES)
        ListCtrlAutoWidthMixin.__init__(self)
        self._parent = parent
        self.populate(columns, data)

    def populate(self, columns, data):
        for i, name in enumerate(columns):
            self.InsertColumn(i, name)
            self.SetColumnWidth(i, 200)
        self.insert_data(data)
        
    def insert_data(self, data):
        for row, item in enumerate(data):
            rowdata = self._parent.get_column_values(item)
            self.InsertStringItem(row, rowdata[0])
            for i in range(1, len(rowdata)):
                data = rowdata[i] is not None and rowdata[i] or ''
                self.SetStringItem(row, i, data)
                
    def update_item(self, index, data):
        self.SetItemText(index, data[0])
        for col in range(1, len(data)):
            self.SetStringItem(index, col, data[col])
