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
from wx import grid

from robotide.publish import RideGridCellChanged
from robotide.utils import PopupMenu

from grid import GridEditor
from contentassist import ExpandingContentAssistTextCtrl
from popupwindow import RidePopupWindow


class KeywordEditorUi(GridEditor):

    def __init__(self, parent, num_rows, num_cols):
        GridEditor.__init__(self, parent)
        self.SetRowLabelSize(25)
        self.SetColLabelSize(0)
        self.SetDefaultColSize(170)
        self.SetDefaultCellOverflow(False)
        self.SetDefaultRenderer(grid.GridCellAutoWrapStringRenderer())
        self.CreateGrid(num_rows, num_cols)
        self.Bind(grid.EVT_GRID_LABEL_RIGHT_CLICK, self.OnLabelRightClick)

    def write_cell(self, row, col, value, update_history=True):
        previous = self.GetCellValue(row, col)
        self._expand_if_necessary(row, col)
        GridEditor.write_cell(self, row, col, value, update_history)
        RideGridCellChanged(cell=(row, col), value=value, previous=previous,
                            grid=self).publish()

    def _expand_if_necessary(self, row, col):
        if row >= self.NumberRows-1:
            self.AppendRows(2)
            self.SetSize(self.GetBestSize())
            self.GetParent().GetSizer().Fit(self.GetParent())
            self.GetGrandParent().GetSizer().Layout()
        if col >= self.NumberCols-1:
            self.AppendCols(1)

    def _remove_selected_rows(self):
        """If whole row(s) are selected, remove them from the grid"""
        for row in sorted(self.GetSelectedRows(), reverse=True):
            self.DeleteRows(row, 1)

    def _get_selected_rows(self):
        rows = self.GetSelectedRows()
        if not rows:
            rows = self._active_row and [self._active_row] or \
                    [self.selection.topleft.row]
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
            self.write_cell(row, col, value)

    def _uncomment_row(self, row):
        if self.GetCellValue(row, 0).lower() == 'comment':
            for col in range(1, self.GetNumberCols()):
                self.write_cell(row, col-1, self.GetCellValue(row, col))
            self.write_cell(row, self.GetNumberCols()-1, '')

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
        self._active_row = self._active_col = None
        self._popup = RidePopupWindow(self, (500,200))
        self._make_bindings()
        self._write_keywords(keywords)
        self._tree = tree

    def _make_bindings(self):
        self.Bind(grid.EVT_GRID_EDITOR_SHOWN, self.OnEditor)
        self.Bind(wx.EVT_KEY_DOWN, self.OnKey)
        self.Bind(wx.EVT_IDLE, self.OnIdle)
        self.Bind(grid.EVT_GRID_CELL_LEFT_CLICK, self.OnCellLeftClick)
        self.Bind(grid.EVT_GRID_CELL_LEFT_DCLICK, self.OnCellLeftDClick)

    def _write_keywords(self, keywords):
        self._write_data([kw.get_display_value() for kw in keywords],
                         update_history=False)

    def OnCopy(self, event=None):
        self.copy()

    def OnCut(self, event=None):
        self.cut()
        self._save_keywords()
        self.set_dirty()

    def OnDelete(self, event=None):
        self.delete()
        self._save_keywords()
        self.set_dirty()

    def OnPaste(self, event=None):
        self.paste()
        self._save_keywords()
        self.set_dirty()

    def OnUndo(self, event=None):
        self.undo()
        self._save_keywords()
        self.set_dirty()

    def set_dirty(self):
        # TODO: it would be better to not set dirty directly
        self._datafile.dirty = True
        self._tree.mark_dirty(self._datafile)

    def save(self):
        self._hide_tooltip()
        if self.IsCellEditControlShown():
            cell_editor = self.GetCellEditor(*self.selection.cell)
            cell_editor.EndEdit(self.selection.topleft.row,
                                self.selection.topleft.col, self)
        self._save_keywords()

    def _save_keywords(self):
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

    def show_content_assist(self):
        if self.IsCellEditControlShown():
            self.GetCellEditor(*self.selection.cell).show_content_assist()

    def show_keyword_details(self):
        cell_value = self.GetCellValue(*self.selection.cell)
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
        row_height = self.GetRowSize(self.selection.topleft.row)
        self.GetCellEditor(*self.selection.cell).SetHeight(row_height)
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
        if value != self._original_value:
            grid.write_cell(row, col, value)
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
