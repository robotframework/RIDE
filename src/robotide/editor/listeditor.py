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
from robotide.lib.robot.utils.compat import with_metaclass
from wx.lib.mixins.listctrl import ListCtrlAutoWidthMixin
from robotide.controller.ctrlcommands import MoveUp, MoveDown, DeleteItem
from robotide.utils import RideEventHandler
from robotide.widgets import PopupMenu, PopupMenuItems, ButtonWithHandler, Font
from robotide.context import ctrl_or_cmd, bind_keys_to_evt_menu, IS_WINDOWS


class ListEditorBase(wx.Panel):
    _menu = ['Edit', 'Move Up\tCtrl-Up', 'Move Down\tCtrl-Down', '---', 'Delete']
    _buttons = []

    def __init__(self, parent, columns, controller):
        wx.Panel.__init__(self, parent)
        self._controller = controller
        self._selection = wx.NOT_FOUND
        self._create_ui(columns, controller)
        self._make_bindings()
        self._bind_keys()

    def _create_ui(self, columns, data):
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        self._list = self._create_list(columns, data)
        sizer.Add(self._list, 1, wx.EXPAND)
        sizer.Add((5,0))
        sizer.Add(self._create_buttons())
        sizer.Add((5,0))
        self.SetSizer(sizer)
        sizer.Layout()

    def _create_list(self, columns, data):
        return AutoWidthColumnList(self, columns, data)

    def _create_buttons(self):
        sizer = wx.BoxSizer(wx.VERTICAL)
        for label in self._buttons:
            sizer.Add(ButtonWithHandler(self, label, width=120), 0, wx.ALL, 1)
        return sizer

    def _make_bindings(self):
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnItemSelected)
        self.Bind(wx.EVT_LIST_ITEM_DESELECTED , self.OnItemDeselected)
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnEdit)
        self.Bind(wx.EVT_LIST_ITEM_RIGHT_CLICK, self.OnRightClick)
        if IS_WINDOWS:
            self.Bind(wx.EVT_COMMAND_LEFT_CLICK, self.OnLeftClick)
        else:
            self._list.Bind(wx.EVT_LEFT_UP, self.OnLeftClick)

    def OnItemSelected(self, event):
        self._selection = event.GetIndex()

    def OnItemDeselected(self, event):
        self._selection = wx.NOT_FOUND

    def OnEdit(self, event):
        pass

    def OnRightClick(self, event):
        PopupMenu(self, PopupMenuItems(self, self._menu))

    def OnLeftClick(self, event):
        pass

    def _bind_keys(self):
        bind_keys_to_evt_menu(self, self._get_bind_keys())

    def _get_bind_keys(self):
        return [(ctrl_or_cmd(), wx.WXK_UP, self.OnMoveUp),
                (ctrl_or_cmd(), wx.WXK_DOWN, self.OnMoveDown),
                (wx.ACCEL_NORMAL, wx.WXK_WINDOWS_MENU, self.OnRightClick),
                (wx.ACCEL_NORMAL, wx.WXK_DELETE, self.OnDelete)]

    def OnMoveUp(self, event):
        if self._selection < 1:
            return
        self._controller.execute(MoveUp(self._selection))
        self.update_data()
        self._list.Select(self._selection-1, True)

    def OnMoveDown(self, event):
        if self._selection == self._list.GetItemCount() - 1 or not self.is_selected:
            return
        self._controller.execute(MoveDown(self._selection))
        self.update_data()
        self._list.Select(self._selection+1, True)

    def OnDelete(self, event):
        if self.is_selected:
            self._with_column_width_preservation(self._delete_selected)

    def _with_column_width_preservation(self, func):
        widths = []
        for i in range(self._list.GetColumnCount()):
            widths.append(self._list.GetColumnWidth(i))
        func()
        for i in range(self._list.GetColumnCount()):
            self._list.SetColumnWidth(i, widths[i])

    def _delete_selected(self):
        self._controller.execute(DeleteItem(self._selection))
        self._calculate_selection()
        self.update_data()

    def _calculate_selection(self):
        self._selection = min(self._selection,
                              sum(1 for _ in self._controller)-1)

    @property
    def is_selected(self):
        return self._selection != wx.NOT_FOUND

    def update_data(self):
        self._list.DeleteAllItems()
        self._list.insert_data(self._controller)
        self._list.select_and_ensure_visibility(self._selection)

    def select(self, text):
        self._list.select(text)

    def has_link_target(self, controller):
        return False

    def has_error(self, controller):
        return False


# Metaclass fix from http://code.activestate.com/recipes/204197-solving-the-metaclass-conflict/
from robotide.utils.noconflict import classmaker


class ListEditor(with_metaclass(classmaker(), ListEditorBase, RideEventHandler)):
    pass

class AutoWidthColumnList(wx.ListCtrl, ListCtrlAutoWidthMixin):

    def __init__(self, parent, columns, data=None):
        wx.ListCtrl.__init__(self, parent,
                             style=wx.LC_REPORT|wx.NO_BORDER|wx.LC_SINGLE_SEL|wx.LC_HRULES)
        ListCtrlAutoWidthMixin.__init__(self)
        self._parent = parent
        self.populate(columns, data or [])

    def populate(self, columns, data):
        for i, name in enumerate(columns):
            self.InsertColumn(i, name)
        self.insert_data(data)

    def insert_data(self, data):
        self._insert_data(data)
        self._set_column_widths()

    def _insert_data(self, data):
        for row, item in enumerate(data):
            rowdata = self._parent.get_column_values(item)
            if wx.VERSION >= (3, 0, 3, ''):  # DEBUG wxPhoenix
                self.InsertItem(row, rowdata[0])
                for i in range(1, len(rowdata)):
                    data = rowdata[i] is not None and rowdata[i] or ''
                    self.SetItem(row, i, data)
            else:
                self.InsertStringItem(row, rowdata[0])
                for i in range(1, len(rowdata)):
                    data = rowdata[i] is not None and rowdata[i] or ''
                    self.SetStringItem(row, i, data)
            self._add_style(row, item)

    def _set_column_widths(self):
        min_width = self._parent.Parent.plugin.global_settings.get('list col min width', 50)
        max_width = self._parent.Parent.plugin.global_settings.get('list col max width', 120)
        for i in range(self.ColumnCount):
            self.SetColumnWidth(i, -1)
            if self.GetColumnWidth(i) < min_width:
                self.SetColumnWidth(i, min_width)
            if self.GetColumnWidth(i) > max_width:
                self.SetColumnWidth(i, max_width)

    def _add_style(self, row, item):
        if self._parent.has_link_target(item):
            self._add_link_style(row)
        if self._parent.has_error(item):
            self._add_error_style(row)

    def _add_link_style(self, row):
        self._set_row_style(row, font=self._underlined_font(), colour=wx.BLUE)

    def _add_error_style(self, row):
        self._set_row_style(row, colour=wx.RED)

    def _set_row_style(self, row, font=None, colour=None):
        list_item = self.GetItem(row)
        if font:
            list_item.SetFont(font)
        if colour:
            list_item.SetTextColour(colour)
        self.SetItem(list_item)

    def _underlined_font(self):
        font = Font().underlined
        if IS_WINDOWS:
            font.SetPointSize(8)
        return font

    def select(self, text):
        index = self.FindItem(0, text)
        self.select_and_ensure_visibility(index)

    def select_and_ensure_visibility(self, index):
        if index >= 0:
            self.Select(index, on=True)
            self.EnsureVisible(index)
            self.Focus(index)
