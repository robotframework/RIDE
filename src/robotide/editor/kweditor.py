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

from robotide.controller.commands import ChangeCellValue, ClearArea, PasteArea,\
    DeleteRows, AddRows, CommentRows, InsertCells, DeleteCells, UncommentRows
from robotide.publish import RideGridCellChanged
from robotide.utils import PopupMenu, RideEventHandler

from grid import GridEditor
from editordialogs import UserKeywordNameDialog
from contentassist import ExpandingContentAssistTextCtrl
from popupwindow import RideHtmlPopupWindow


class KeywordEditor(GridEditor, RideEventHandler):
    dirty = property(lambda self: self._controller.dirty)
    _no_cell = grid.GridCellCoords(-1, -1)
    _popup_items = ['Create Keyword', 'Extract Keyword', 'Rename Keyword', '---'] + \
            GridEditor._popup_items

    def __init__(self, parent, controller, tree):
        GridEditor.__init__(self, parent, len(controller.steps) + 5, 5)
        self.SetRowLabelSize(25)
        self.SetColLabelSize(0)
        self.SetDefaultColSize(170)
        self.SetDefaultCellOverflow(False)
        self.Bind(grid.EVT_GRID_LABEL_RIGHT_CLICK, self.OnLabelRightClick)
        # This makes it possible to select cell 0,0 without opening editor, issue 479
        self.SetGridCursor(self.NumberRows - 1, self.NumberCols - 1)
        self.SetDefaultEditor(ContentAssistCellEditor(parent.plugin))
        self._controller = controller
        self._controller.add_change_listener(self._data_changed)
        # TODO: Tooltip may be smaller when the documentation is wrapped correctly
        self._tooltip = RideHtmlPopupWindow(self, (650, 400))
        self._marked_cell = None
        self._idle_mouse_cell = self._no_cell
        self._active_row = self._active_col = None
        self._make_bindings()
        self._write_steps(self._controller)
        self._tree = tree
        self._plugin = parent.plugin

    def write_cell(self, row, col, value, update_history=True):
        previous = self.GetCellValue(row, col) \
                if (row < self.NumberRows and col < self.NumberCols) else ''
        GridEditor.write_cell(self, row, col, value, update_history)
        RideGridCellChanged(cell=(row, col), value=value, previous=previous,
                            grid=self).publish()

    def _remove_selected_rows(self):
        """If whole row(s) are selected, remove them from the grid"""
        self._update_history()
        for row in sorted(self.selection.rows(), reverse=True):
            self.DeleteRows(row, 1)

    def _toggle_underlined(self, cell):
        font = self.GetCellFont(cell.Row, cell.Col)
        font.SetUnderlined(not font.Underlined)
        self.SetCellFont(cell.Row, cell.Col, font)
        self.Refresh()

    def OnLabelRightClick(self, event):
        self._active_row = event.GetRow()
        PopupMenu(self, ['Insert Rows', 'Delete Rows\tDel',
                         'Comment Rows\tCtrl-3', 'Uncomment Rows\tCtrl-4'])
        self._active_row = None
        event.Skip()

    def OnInsertRows(self, event):
        self._controller.execute(AddRows(self.selection.rows()))
        event.Skip()

    def OnInsertCells(self, event):
        self._controller.execute(InsertCells(self.selection.topleft,
                                             self.selection.bottomright))
        event.Skip()

    def OnDeleteCells(self, event):
        self._controller.execute(DeleteCells(self.selection.topleft,
                                             self.selection.bottomright))
        event.Skip()

    def OnCommentRows(self, event):
        self._controller.execute(CommentRows(self.selection.rows()))
        event.Skip()

    def OnUncommentRows(self, event):
        self._controller.execute(UncommentRows(self.selection.rows()))
        event.Skip()

    def _make_bindings(self):
        self.Bind(grid.EVT_GRID_EDITOR_SHOWN, self.OnEditor)
        self.Bind(wx.EVT_KEY_DOWN, self.OnKey)
        self.Bind(wx.EVT_IDLE, self.OnIdle)
        self.Bind(grid.EVT_GRID_CELL_LEFT_CLICK, self.OnCellLeftClick)
        self.Bind(grid.EVT_GRID_CELL_LEFT_DCLICK, self.OnCellLeftDClick)

    def _data_changed(self, controller):
        self._write_steps(controller)
        self.set_dirty()

    def _write_steps(self, controller):
        data = []
        for step in controller.steps:
            data.append(self._format_comments(step.as_list()))
        self.ClearGrid()
        self._write_data(data, update_history=False)

    def _format_comments(self, data):
        # TODO: This should be moved to robot.model
        in_comment = False
        ret = []
        for cell in data:
            if cell.strip().startswith('#'):
                in_comment = True
            if in_comment:
                cell = cell.replace(' |', '')
            ret.append(cell)
        return ret

    def cell_value_edited(self, row, col, value):
        self._controller.execute(ChangeCellValue(row, col, value))

    def get_selected_datafile_controller(self):
        return self._controller.datafile_controller

    def OnCopy(self, event=None):
        self.copy()

    def OnCut(self, event=None):
        self._clipboard_handler.cut()
        self.OnDelete(event)

    def OnDelete(self, event=None):
        self._controller.execute(ClearArea(self.selection.topleft,
                                           self.selection.bottomright))

    def OnPaste(self, event=None):
        data = self._clipboard_handler.clipboard_content()
        if data:
            data = [[data]] if isinstance(data, basestring) else data
            self._controller.execute(PasteArea(self.selection.topleft, data))

    def OnDeleteRows(self, event):
        self._controller.execute(DeleteRows(self.selection.rows()))
        event.Skip()

    def OnUndo(self, event=None):
        raise NotImplementedError()
        self.undo()
        self.set_dirty()

    def set_dirty(self):
        self._controller.mark_dirty()
        self._tree.mark_dirty(self._controller)

    def close(self):
        self.save()
        self._controller.remove_change_listener(self._data_changed)

    def save(self):
        self.hide_tooltip()
        if self.IsCellEditControlShown():
            cell_editor = self.GetCellEditor(*self.selection.cell)
            cell_editor.EndEdit(self.selection.topleft.row,
                                self.selection.topleft.col, self)

    def show_content_assist(self):
        if self.IsCellEditControlShown():
            self.GetCellEditor(*self.selection.cell).show_content_assist()

    def _calculate_position(self):
        x, y = wx.GetMousePosition()
        return x, y + 20

    def OnEditor(self, event):
        row_height = self.GetRowSize(self.selection.topleft.row)
        self.GetCellEditor(*self.selection.cell).SetHeight(row_height)
        event.Skip()

    def OnKey(self, event):
        # TODO: Cleanup
        keycode, control_down = event.GetKeyCode(), event.CmdDown()
        if keycode == ord('A') and control_down:
            self.OnSelectAll(event)
            return
        if keycode == wx.WXK_CONTROL and self._tooltip.IsShown():
            return
        self.hide_tooltip()
        if keycode == wx.WXK_WINDOWS_MENU:
            self.OnCellRightClick(event)
            return
        if control_down or keycode not in [wx.WXK_RETURN, wx.WXK_BACK]:
            event.Skip()
            return
        self.DisableCellEditControl()
        if keycode == wx.WXK_RETURN:
            self.MoveCursorRight(event.ShiftDown())
        else:
            self.MoveCursorLeft(event.ShiftDown())

    def OnSelectAll(self, event):
        self.SelectAll()

    def OnCellLeftClick(self, event):
        self.hide_tooltip()
        if event.ControlDown():
            if not self._navigate_to_matching_user_keyword(event.Row, event.Col):
                event.Skip()
        else:
            event.Skip()

    def OnCellLeftDClick(self, event):
        self.hide_tooltip()
        if not self._navigate_to_matching_user_keyword(event.Row, event.Col):
            event.Skip()

    def _navigate_to_matching_user_keyword(self, row, col):
        value = self.GetCellValue(row, col)
        uk = self._plugin.get_user_keyword(value)
        if uk:
            self._toggle_underlined((grid.GridCellCoords(row, col)))
            self._marked_cell = None
            self._tree.select_user_keyword_node(uk)
            return True
        return False

    def OnIdle(self, evt):
        if not self._is_active_window() or self.IsCellEditControlShown():
            self.hide_tooltip()
            return
        cell = self._cell_under_cursor()
        if cell == self._no_cell:
            return
        if not wx.GetMouseState().ControlDown():
            self.hide_tooltip()
            self._hide_link_if_necessary(cell)
            return
        self._idle_mouse_cell = cell
        self._hide_link_if_necessary(cell)
        self._show_possible_user_keyword_link(cell)
        if not self._tooltip.IsShown():
            self._show_kw_tooltip(cell)

    def _is_active_window(self):
        return self.IsShownOnScreen() and self.FindFocus()

    def _cell_under_cursor(self):
        pos = self.CalcUnscrolledPosition(self.ScreenToClient(wx.GetMousePosition()))
        return self.XYToCell(*pos)

    def _show_possible_user_keyword_link(self, cell):
        if cell == self._marked_cell:
            return
        value = self.GetCellValue(cell.Row, cell.Col)
        if not self._plugin.get_user_keyword(value):
            return
        self._toggle_underlined(cell)
        self._marked_cell = cell

    def _hide_link_if_necessary(self, cell):
        if not self._marked_cell:
            return
        if cell != self._marked_cell:
            self._toggle_underlined(self._marked_cell)
            self._marked_cell = None

    def _show_kw_tooltip(self, cell):
        value = self.GetCellValue(cell.Row, cell.Col)
        details = self._plugin.get_keyword_details(value)
        if not details:
            return
        self._tooltip.set_content(details)
        point = self.CellToRect(cell.Row, cell.Col).GetTopRight()
        point.x += self.GetRowLabelSize() + 5
        point = self.CalcScrolledPosition(point)
        self._tooltip.SetPosition(self.ClientToScreen(point))
        self._tooltip.Show()

    def hide_tooltip(self):
        if self._tooltip and self._tooltip.IsShown():
            self._tooltip.Show(False)

    def OnCreateKeyword(self, event):
        name, args = self._name_and_args_for_new_keyword()
        try:
            self._controller.create_user_keyword(name, args,
                                                 self._tree.add_keyword_controller)
        except ValueError, err:
            wx.MessageBox(unicode(err))

    def _name_and_args_for_new_keyword(self):
        data_cells = self._data_cells_from_current_row()
        if not data_cells:
            return '', []
        return data_cells[0], data_cells[1:]

    def _data_cells_from_current_row(self):
        currow, curcol = self.selection.cell
        rowdata = self._row_data(currow)
        return self._strip_trailing_empty_cells(self._remove_comments(rowdata[curcol:]))

    def _remove_comments(self, data):
        for index, cell in enumerate(data):
            if cell.strip().startswith('#'):
                return data[:index]
        return data

    def OnExtractKeyword(self, event):
        dlg = UserKeywordNameDialog(self._controller)
        if dlg.ShowModal() == wx.ID_OK:
            self._extract_keyword(*dlg.get_value())

    def _extract_keyword(self, name, args):
        rows = self.selection.topleft.row, self.selection.bottomright.row
        self._controller.extract_keyword(name, args, rows,
                                         self._tree.add_keyword_controller)
        raise RuntimeError('Please fix me')
        self._write_keywords(self._controller.steps)

    def OnRenameKeyword(self, event):
        from robotide.controller import RenameOccurrences
        old_name = self._current_cell_value()
        new_name = wx.GetTextFromUser('New name', default_value=old_name)
        if new_name:
            self._controller.execute(RenameOccurrences(old_name, new_name))
            wx.CallAfter(self._plugin.OnTreeItemSelected)


class ContentAssistCellEditor(grid.PyGridCellEditor):

    def __init__(self, plugin):
        grid.PyGridCellEditor.__init__(self)
        self._plugin = plugin
        self._grid = None

    def show_content_assist(self):
        self._tc.show_content_assist()

    def Create(self, parent, id, evthandler):
        self._tc = ExpandingContentAssistTextCtrl(parent, self._plugin)
        self.SetControl(self._tc)
        if evthandler:
            self._tc.PushEventHandler(evthandler)

    def SetSize(self, rect):
        self._tc.SetDimensions(rect.x, rect.y, rect.width + 2, rect.height + 2,
                               wx.SIZE_ALLOW_MINUS_ONE)

    def SetHeight(self, height):
        self._height = height

    def BeginEdit(self, row, col, grid):
        self._tc.SetSize((-1, self._height))
        self._original_value = grid.GetCellValue(row, col)
        self._grid = grid
        self.StartingClick()

    def EndEdit(self, row, col, grid):
        if self._tc.content_assist_value():
            value = self._tc.content_assist_value()
        else:
            value = self._tc.GetValue()
        if value != self._original_value:
            grid.cell_value_edited(row, col, value)
        self._tc.hide()
        grid.SetFocus()
        return True

    def Reset(self):
        self._tc.SetValue(self._original_value)
        self._tc.reset()

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
