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

import os
from wx import grid
import wx

from robotide.publish import RideGridCellChanged
from robotide.utils import ExpandingContentAssistTextCtrl, RidePopupWindow,\
    PopupMenu

from clipboard import GRID_CLIPBOARD


class KeywordEditorUi(grid.Grid):

    def __init__(self, parent, num_rows, num_cols):
        grid.Grid.__init__(self, parent)
        self.SetRowLabelSize(25)
        self.SetColLabelSize(0)
        self.SetDefaultColSize(170)
        self.SetDefaultCellOverflow(False)
        self.SetDefaultRenderer(grid.GridCellAutoWrapStringRenderer())
        self.CreateGrid(num_rows, num_cols)
        self.Bind(grid.EVT_GRID_LABEL_RIGHT_CLICK, self.OnLabelRightClick)
        self.Bind(grid.EVT_GRID_SELECT_CELL, self.OnSelectCell)
        self.Bind(grid.EVT_GRID_RANGE_SELECT, self.OnRangeSelect)
        self._edit_history = []

    def write_cell(self, celldata, row, col):
        if row >= self.GetNumberRows():
            self.AppendRows(2)
            self.SetSize(self.GetBestSize())
            self.GetParent().GetSizer().Fit(self.GetParent())
            self.GetGrandParent().GetSizer().Layout()
        if col >= self.GetNumberCols():
            self.AppendCols(1)
        self.SetCellValue(row, col, celldata)

    def SetCellValue(self, row, col, value, send_event=True):
        previous = self.GetCellValue(row, col)
        grid.Grid.SetCellValue(self, row, col, value)
        if send_event:
            RideGridCellChanged(cell=(row, col), value=value, previous=previous,
                                grid=self).publish()

    def OnCut(self, event=None):
        """Cuts the contents of the selected cell(s). This does a normal cut
        action if the user is editing a cell, otherwise it places the selected
        range of cells on the clipboard.
        """
        if self.IsCellEditControlShown():
            # This is needed in Windows
            self._get_cell_edit_control().Cut()
            self._save_keywords()
            self.set_dirty()
        else:
            self._move_to_clipboard(delete=True)
            self._remove_selected_rows()

    def OnCopy(self, event=None):
        """Copy the contents of the selected cell(s). This does a normal copy
        action if the user is editing a cell, otherwise it places the selected
        range of cells on the clipboard.
        """
        if self.IsCellEditControlShown():
            # This is needed in Windows
            self._get_cell_edit_control().Copy()
        else:
            self._move_to_clipboard()

    def OnPaste(self, event=None):
        """Paste the contents of the clipboard. If a cell is being edited just
        do a normal paste. If a cell is not being edited, paste whole rows.
        """
        clipboard = GRID_CLIPBOARD.get_contents()
        if self.IsCellEditControlShown():
            # This is needed in Windows
            if isinstance(clipboard, list):
                cells_as_text = ' '.join([' '.join(row) for row in clipboard])
                self._get_cell_edit_control().WriteText(cells_as_text)
            # FIXME: there must be a better way to prevent double pasting on
            # linux, also this breaks the pasting via menu
            elif os.name == 'nt':
                self._get_cell_edit_control().Paste()
        else:
            if not clipboard:
                return
            cell = self._active_coords.topleft
            if not isinstance(clipboard, list):
                self.write_cell(clipboard, cell.row, cell.col)
            else:
                row = cell.row
                for datarow in clipboard:
                    col = cell.col
                    for data in datarow:
                        self.write_cell(data, row, col)
                        col += 1
                    row += 1
        self._save_keywords()
        self.set_dirty()

    def OnDelete(self, event=None):
        if self.IsCellEditControlShown():
            # This is needed in Windows
            editor = self._get_cell_edit_control()
            start, end = editor.GetSelection()
            if start == end:
                end += 1
            editor.Remove(start, end)
            if event:
                event.Skip()
        else:
            self._move_to_clipboard(copy=False, delete=True)
                
    def undo(self):
        if self._edit_history:
            self.ClearGrid()
            self._write_data(self._edit_history.pop())
            self._save_keywords(append_to_history=False)

    def _get_cell_edit_control(self):
        return self.GetCellEditor(*self._active_coords.cell).GetControl()

    def _move_to_clipboard(self, copy=True, delete=False):
        if self._active_coords is None:
            return
        clipboard = []
        startrow = self._active_coords.topleft.row
        startcol = self._active_coords.topleft.col
        endrow = self._active_coords.bottomright.row
        endcol = self._active_coords.bottomright.col
        row = []
        for i in range(endrow-startrow+1):
            for j in range(endcol-startcol+1):
                row.append(self.GetCellValue(startrow+i, startcol+j))
                if delete:
                    self.write_cell('', startrow+i, startcol+j)
            if copy:
                clipboard.append(row)
            row = []
        if delete:
            self.set_dirty()
            self._save_keywords()
            self._remove_selected_rows()
        if len(clipboard) > 0:
            if self._is_single_cell_data(clipboard) and os.name == 'nt':
                self._add_single_cell_data_to_clipboard(clipboard)
            else:
                GRID_CLIPBOARD.set_contents(clipboard)

    def _is_single_cell_data(self, clipboard):
        return len(clipboard) == 1 and len(clipboard[0]) == 1

    def _add_single_cell_data_to_clipboard(self, data_table):
        #TODO: This should be moved to clipboard module
        do = wx.TextDataObject()
        do.SetText(data_table[0][0])
        wx.TheClipboard.Open()
        wx.TheClipboard.AddData(do)
        wx.TheClipboard.Close()

    def _remove_selected_rows(self):
        """If whole row(s) are selected, remove them from the grid"""
        for row in sorted(self.GetSelectedRows(), reverse=True):
            self.DeleteRows(row, 1)

    def _get_selected_rows(self):
        rows = self.GetSelectedRows()
        if not rows:
            rows = self._active_row and [self._active_row] or \
                    [self._active_coords.topleft.row]
        return rows

    def _set_cell_font(self, cell, color=None, underlined=False):
        if not color:
            color = self.GetDefaultCellTextColour()
        font = self.GetDefaultCellFont()
        font.SetUnderlined(underlined)
        self.SetCellFont(cell.Row, cell.Col, font)
        self.SetCellTextColour(cell.Row, cell.Col, color)
        self.Refresh()

    def comment(self):
        self._do_action_on_selected_rows(self._comment_row)

    def uncomment(self):
        self._do_action_on_selected_rows(self._uncomment_row)

    def _comment_row(self, row):
        rowdata = [ self.GetCellValue(row, col) for col in range(self.NumberCols) ]
        rowdata = ['Comment'] + self._strip_trailing_empty_cells(rowdata)
        if rowdata[-1]:
            self.InsertCols(self.GetNumberCols())
        for col, value in enumerate(rowdata):
            self.SetCellValue(row, col, value)

    def _uncomment_row(self, row):
        if self.GetCellValue(row, 0).lower() == 'comment':
            for col in range(1, self.GetNumberCols()):
                self.SetCellValue(row, col-1, self.GetCellValue(row, col))
            self.SetCellValue(row, self.GetNumberCols()-1, '')

    def _do_action_on_selected_rows(self, action):
        for row in self._get_selected_rows():
            action(row)
        self.set_dirty()

    def OnLabelRightClick(self, event):
        self._active_row = event.GetRow()
        PopupMenu(self, ['Insert Rows', 'Delete Rows\tDel',
                         'Comment Rows\tCtrl-3', 'Uncomment Rows\tCtrl-4'])
        self._active_row = None
        event.Skip()

    def OnSelectCell(self, event):
        self._active_coords = _GridCoords((event.GetRow(), event.GetCol()))
        self.AutoSizeRows()
        event.Skip()

    def OnRangeSelect(self, event):
        if event.Selecting():
            row_selection = self.GetSelectedRows()
            if row_selection:
                topleft  = row_selection[0], 0
                bottomright = row_selection[-1], self.GetNumberCols()-1
            else:
                topleft = event.GetTopLeftCoords().GetRow(), event.GetTopLeftCoords().GetCol()
                bottomright = event.GetBottomRightCoords().GetRow(), event.GetBottomRightCoords().GetCol()
            self._active_coords = _GridCoords(topleft, bottomright)
        event.Skip()

    def OnInsertRows(self, event):
        self.InsertRows(*self._get_insertion_position_and_row_count(event))
        self.GetParent().Sizer.Layout()
        event.Skip()

    def _get_insertion_position_and_row_count(self, event):
        if isinstance(event.EventObject, wx.Button):
            return self.GetNumberRows(), 1
        rows = self._get_selected_rows()
        return min(rows), len(rows)

    def OnDeleteRows(self, event):
        self.set_dirty()
        self._remove_selected_rows()
        self.GetParent().Sizer.Layout()
        event.Skip()

    def OnCommentRows(self, event):
        self.comment()
        event.Skip()

    def OnUncommentRows(self, event):
        self.uncomment()
        event.Skip()

    def OnInsertCol(self, event):
        if isinstance(event.EventObject, wx.Button):
            col = self.GetNumberCols()
        else:
            col = self._active_col
        self.InsertCols(col, 1)
        self.GetParent().Sizer.Layout()
        event.Skip()

    def OnDeleteCol(self, event):
        self.set_dirty()
        self.DeleteCols(self._active_col, 1)
        self.GetParent().Sizer.Layout()
        event.Skip()


class KeywordEditor(KeywordEditorUi):
    _no_cell = grid.GridCellCoords(-1, -1)

    def __init__(self, parent, keywords, tree):
        KeywordEditorUi.__init__(self, parent, len(keywords)+5, 5)
        self.SetDefaultEditor(ContentAssistCellEditor(keywords.datafile))
        self._keywords = keywords
        self._datafile = keywords.datafile
        # TODO: Tooltip may be smaller when the documentation is wrapped correctly
        self._tooltip = RidePopupWindow(self, (650, 400))
        self._marked_cell = None
        self._idle_mouse_cell = self._no_cell
        self._active_coords = _GridCoords((0, 0))
        self._active_row = self._active_col = None
        self._popup = RidePopupWindow(self, (500,200))
        self._make_bindings()
        self._write_data(keywords)
        self._tree = tree

    def _make_bindings(self):
        self.Bind(grid.EVT_GRID_EDITOR_SHOWN, self.OnEditor)
        self.Bind(wx.EVT_KEY_DOWN, self.OnKey)
        self.Bind(wx.EVT_IDLE, self.OnIdle)
        self.Bind(grid.EVT_GRID_CELL_LEFT_CLICK, self.OnCellLeftClick)
        self.Bind(grid.EVT_GRID_CELL_LEFT_DCLICK, self.OnCellLeftDClick)
        self.Bind(grid.EVT_GRID_CELL_RIGHT_CLICK, self.OnCellRightClick)

    def _write_data(self, keywords):
        for row, kw in enumerate(keywords):
            for col, arg in enumerate(kw.get_display_value()):
                self.write_cell(arg, row, col)
        self.AutoSizeRows()

    def set_dirty(self):
        # TODO: it would be better to not set dirty directly
        self._datafile.dirty = True
        self._tree.mark_dirty(self._datafile)

    def save(self):
        self._hide_tooltip()
        if self.IsCellEditControlShown():
            cell_editor = self.GetCellEditor(*self._active_coords.cell)
            cell_editor.EndEdit(self._active_coords.topleft.row, self._active_coords.topleft.col, self)
        self._save_keywords()

    def _save_keywords(self, append_to_history=True):
        if append_to_history:
            self._edit_history.append(self._keywords[:])
        kwdata = []
        for i in range(self.GetNumberRows()):
            rowdata = []
            for j in range(self.GetNumberCols()):
                cellvalue = self.GetCellValue(i, j).replace('\n', ' ')
                rowdata.append(cellvalue)
            rowdata = self._strip_trailing_empty_cells(rowdata)
            if rowdata:
                kwdata.append(rowdata)
        self._keywords.parse_keywords_from_grid(kwdata)

    def _strip_trailing_empty_cells(self, rowdata):
        while rowdata and not rowdata[-1]:
            rowdata.pop()
        return rowdata

    def show_content_assist(self):
        if self.IsCellEditControlShown():
            self.GetCellEditor(*self._active_coords.cell).show_content_assist()

    def show_keyword_details(self):
        cell_value = self.GetCellValue(*self._active_coords.cell)
        kw = self._datafile.get_keywords_for_content_assist(name=cell_value)
        if kw:
            self._popup.SetPosition(self._calculate_position())
            text = 'Source: %s<br><br>Arguments: %s<br><br>%s' % (kw.source, kw.args, kw.doc)
            self._popup.set_content(text)
            self._popup.Show()

    def _calculate_position(self):
        x, y = wx.GetMousePosition()
        return x, y + 20

    def hide_popup(self):
        if self._popup.IsShown():
            self._popup.Show(False)

    def OnEditor(self, event):
        row_height = self.GetRowSize(self._active_coords.topleft.row)
        self.GetCellEditor(*self._active_coords.cell).SetHeight(row_height)
        event.Skip()

    def OnKey(self, event):
        if event.ControlDown() and self._tooltip.IsShown():
            return
        self._hide_tooltip()
        self.hide_popup()
        if event.ControlDown() or event.GetKeyCode() not in [wx.WXK_RETURN, wx.WXK_BACK]:
            event.Skip()
            return
        self.DisableCellEditControl()
        if event.GetKeyCode() == wx.WXK_RETURN:
            self.MoveCursorRight(event.ShiftDown())
        else:
            self.MoveCursorLeft(event.ShiftDown())

    def OnCellLeftClick(self, event):
        self._hide_tooltip()
        self.hide_popup()
        if event.ControlDown():
            if not self._navigate_to_matching_user_keyword(event.Row, event.Col):
                event.Skip()
        else:
            event.Skip()

    def OnCellLeftDClick(self, event):
        self._hide_tooltip()
        self.hide_popup()
        if not self._navigate_to_matching_user_keyword(event.Row, event.Col):
            event.Skip()

    def _navigate_to_matching_user_keyword(self, row, col):
        value = self.GetCellValue(row, col)
        uk = self._datafile.get_user_keyword(value)
        if uk:
            self._set_cell_font((grid.GridCellCoords(row, col)))
            self._marked_cell = None
            self._tree.select_user_keyword_node(uk)
            return True
        return False

    def OnCellRightClick(self, event):
        PopupMenu(self, ['Cut\tCtrl-X', 'Copy\tCtrl-C', 'Paste\tCtrl-V', '---',
                         'Delete\tDel'])

    def OnIdle(self, evt):
        if not self.IsShownOnScreen() or self.IsCellEditControlShown():
            return
        pos = self.CalcUnscrolledPosition(self.ScreenToClient(wx.GetMousePosition()))
        cell = self.XYToCell(*pos)
        if cell == self._no_cell:
            return
        if not wx.GetMouseState().ControlDown():
            self._hide_tooltip()
            self._hide_link_if_necessary(cell)
            return
        self._idle_mouse_cell = cell
        self._hide_link_if_necessary(cell)
        self._show_possible_user_keyword_link(cell)
        if not self._tooltip.IsShown():
            self._show_kw_tooltip(cell)

    def _show_possible_user_keyword_link(self, cell):
        if cell == self._marked_cell:
            return
        value = self.GetCellValue(cell.Row, cell.Col)
        if not self._datafile.get_user_keyword(value):
            return
        self._set_cell_font(cell, color='Blue', underlined=True)
        self._marked_cell = cell

    def _hide_link_if_necessary(self, cell):
        if not self._marked_cell:
            return
        if cell != self._marked_cell:
            self._set_cell_font(self._marked_cell)
            self._marked_cell = None

    def _show_kw_tooltip(self, cell):
        value = self.GetCellValue(cell.Row, cell.Col)
        kws = self._datafile.get_keywords_for_content_assist(name=value)
        # TODO: Handle multiple return values.
        if len(kws) != 1:
            return
        self._tooltip.set_content(kws[0].get_details())
        point = self.CellToRect(cell.Row, cell.Col).GetTopRight()
        point.x += self.GetRowLabelSize() + 5
        point = self.CalcScrolledPosition(point)
        self._tooltip.SetPosition(self.ClientToScreen(point))
        self._tooltip.Show()

    def _hide_tooltip(self):
        if self._tooltip and self._tooltip.IsShown():
            self._tooltip.Show(False)


class _GridCoords(object):

    def __init__(self, topleft, bottomright=None):
        self.topleft = _Cell(*topleft)
        if bottomright is None:
            bottomright = topleft
        self.bottomright = _Cell(*bottomright)
        self.cell = (self.topleft.row, self.topleft.col)


class _Cell(object):

    def __init__(self, row, col):
        self.row = row
        self.col = col


class ContentAssistCellEditor(grid.PyGridCellEditor):

    def __init__(self, item):
        grid.PyGridCellEditor.__init__(self)
        self._item = item
        self._grid = None
        self._previous_value = None

    def show_content_assist(self):
        self._tc.show_content_assist()

    def Create(self, parent, id, evthandler):
        self._tc = ExpandingContentAssistTextCtrl(parent, self._item)
        self._tc.Bind(wx.EVT_TEXT, self.OnText, self._tc)
        self.SetControl(self._tc)
        if evthandler:
            self._tc.PushEventHandler(evthandler)

    def SetSize(self, rect):
        self._tc.SetDimensions(rect.x, rect.y, rect.width+2, rect.height+2,
                               wx.SIZE_ALLOW_MINUS_ONE)

    def SetHeight(self, height):
        self._height = height

    def BeginEdit(self, row, col, grid):
        self._tc.SetSize((-1, self._height))
        self._original_value = self._previous_value = grid.GetCellValue(row, col)
        self._grid = grid
        self.StartingClick()

    def EndEdit(self, row, col, grid):
        if self._tc.content_assist_value():
            value = self._tc.content_assist_value()
        else:
            value = self._tc.GetValue()
        grid.SetCellValue(row, col, value)
        if value != self._previous_value:
            grid.set_dirty()
        self._previous_value = value
        self._tc.hide()
        return True

    def Reset(self):
        self._tc.SetValue(self._original_value)
        self._tc._selection = -1

    def StartingKey(self, event):
        key = event.GetKeyCode()
        if key is wx.WXK_DELETE or key > 255:
            self._grid.HideCellEditControl()
            return
        self._tc.SetValue(unichr(key))
        self._tc.SetFocus()
        self._tc.SetInsertionPointEnd()

    def StartingClick(self):
        self._tc.SetValue(self._original_value)
        self._tc.SelectAll()
        self._tc.SetFocus()

    def Clone(self):
        return ContentAssistCellEditor()

    def OnText(self, event):
        if self._previous_value != self._tc.GetValue() and self._grid:
            self._grid.set_dirty()
        self._previous_value = self._tc.GetValue()
        event.Skip()
