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

from robotide.controller.commands import (ChangeCellValue, ClearArea, PasteArea,
                                          DeleteRows, AddRows, CommentRows,
                                          InsertCells, DeleteCells,
                                          UncommentRows, Undo, Redo,
                                          RenameKeywordOccurrences,
                                          ExtractKeyword, AddKeywordFromCells,
                                          MoveRowsUp, MoveRowsDown,
                                          ExtractScalar, ExtractList)
from robotide.controller.cellinfo import TipMessage
from robotide.publish import RideGridCellChanged, RideItemStepsChanged, PUBLISHER
from robotide.utils import RideEventHandler
from robotide.widgets import PopupMenu, PopupMenuItems
from robotide.context import SETTINGS # TODO: can we avoid direct reference?
from robot.parsing.model import Variable

from robotide.editor.grid import GridEditor
from robotide.editor.tooltips import GridToolTips
from robotide.editor.editordialogs import (UserKeywordNameDialog,
                                           ScalarVariableDialog,
                                           ListVariableDialog)
from robotide.editor.contentassist import ExpandingContentAssistTextCtrl
from robotide.editor.gridcolorizer import Colorizer, ColorizationSettings


class KeywordEditor(GridEditor, RideEventHandler):
    _no_cell = (-1,-1)
    _popup_menu_shown = False
    dirty = property(lambda self: self._controller.dirty)
    _popup_items = ['Create Keyword', 'Extract Keyword', 'Extract Variable', 'Rename Keyword',
                    '---'] + GridEditor._popup_items

    def __init__(self, parent, controller, tree):
        try:
            GridEditor.__init__(self, parent, len(controller.steps) + 5,
                                max((controller.max_columns + 1), 5),
                                parent.plugin._grid_popup_creator)
            self._parent = parent
            self._plugin = parent.plugin
            self._cell_selected = False
            self._colorizer = Colorizer(self, controller, ColorizationSettings(SETTINGS))
            self._configure_grid()
            self._controller = controller
            PUBLISHER.subscribe(self._data_changed, RideItemStepsChanged)
            self._tooltips = GridToolTips(self)
            self._marked_cell = None
            self._active_row = self._active_col = None
            self._make_bindings()
            self._write_steps(self._controller)
            self._tree = tree
            self._has_been_clicked = False
        except Exception, e:
            print 'Exception in initing KeywordEditor: %s' % e
            raise

    def _configure_grid(self):
        self.SetRowLabelSize(25)
        self.SetColLabelSize(0)
        self.SetDefaultColSize(170)
        self.SetDefaultCellOverflow(False)
        self.SetDefaultEditor(ContentAssistCellEditor(self._plugin))

    def _make_bindings(self):
        self.Bind(grid.EVT_GRID_EDITOR_SHOWN, self.OnEditor)
        self.Bind(wx.EVT_KEY_DOWN, self.OnKeyDown)
        self.Bind(wx.EVT_KEY_UP, self.OnKeyUp)
        self.Bind(grid.EVT_GRID_CELL_LEFT_CLICK, self.OnCellLeftClick)
        self.Bind(grid.EVT_GRID_CELL_LEFT_DCLICK, self.OnCellLeftDClick)
        self.Bind(grid.EVT_GRID_LABEL_RIGHT_CLICK, self.OnLabelRightClick)
        self.Bind(wx.EVT_KILL_FOCUS, self.OnKillFocus)

    def get_tooltip_content(self):
        if self.IsCellEditControlShown() or self._popup_menu_shown:
            return ''
        cell = self._cell_under_cursor()
        cell_info = self._controller.get_cell_info(cell.Row, cell.Col)
        return TipMessage(cell_info)

    def OnSelectCell(self, event):
        self._cell_selected = True
        GridEditor.OnSelectCell(self, event)
        self._colorize_grid()
        event.Skip()

    def OnKillFocus(self, event):
        self._tooltips.hide()
        self._hide_link_if_necessary()

    def _execute(self, command):
        return self._controller.execute(command)

    def write_cell(self, row, col, value, update_history=True):
        previous = self.GetCellValue(row, col) \
                if (row < self.NumberRows and col < self.NumberCols) else ''
        GridEditor.write_cell(self, row, col, value, update_history)
        RideGridCellChanged(cell=(row, col), value=value, previous=previous,
                            grid=self).publish()

    def _toggle_underlined(self, cell):
        font = self.GetCellFont(cell.Row, cell.Col)
        font.SetUnderlined(not font.Underlined)
        self.SetCellFont(cell.Row, cell.Col, font)
        self.Refresh()

    def OnLabelRightClick(self, event):
        self._active_row = event.GetRow()
        popupitems = ['Insert Rows', 'Delete Rows\tDel',
                      'Comment Rows\tCtrl-3', 'Uncomment Rows\tCtrl-4',
                      'Move Rows Up\tAlt-Up', 'Move Rows Down\tAlt-Down']
        PopupMenu(self, PopupMenuItems(self, popupitems))
        self._active_row = None
        event.Skip()

    def OnInsertRows(self, event):
        self._execute(AddRows(self.selection.rows()))
        event.Skip()

    def OnInsertCells(self, event):
        self._execute(InsertCells(self.selection.topleft,
                                  self.selection.bottomright))
        event.Skip()

    def OnDeleteCells(self, event):
        self._execute(DeleteCells(self.selection.topleft,
                                  self.selection.bottomright))
        event.Skip()

    def OnCommentRows(self, event=None):
        self._execute(CommentRows(self.selection.rows()))
        if event is not None:
            event.Skip()

    def OnUncommentRows(self, event=None):
        self._execute(UncommentRows(self.selection.rows()))
        if event is not None:
            event.Skip()

    def OnMoveRowsUp(self, event=None):
        if self._execute(MoveRowsUp(self.selection.rows())):
            self._shift_selection(-1)

    def OnMoveRowsDown(self, event=None):
        if self._execute(MoveRowsDown(self.selection.rows())):
            self._shift_selection(1)

    def OnMotion(self, event):
        pass

    def _shift_selection(self, shift):
        self.ClearSelection()
        for r in self.selection.rows():
            self.SelectRow(r+shift, True)

    def _data_changed(self, data):
        if self._controller == data.item:
            self._write_steps(data.item)

    def _write_steps(self, controller):
        data = []
        for step in controller.steps:
            data.append(self._format_comments(step.as_list()))
        self.ClearGrid()
        self._write_data(data, update_history=False)
        self._colorize_grid()

    def _colorize_grid(self):
        selection_content = self._get_single_selection_content_or_none_on_first_call()
        if selection_content is None:
            self.highlight(selection_content)
        else:
            self._parent.highlight(selection_content)

    def highlight(self, text):
        self._colorizer.colorize(text)

    def _get_single_selection_content_or_none_on_first_call(self):
        if self._cell_selected:
            return self.get_single_selection_content()

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
        self._execute(ChangeCellValue(row, col, value))

    def get_selected_datafile_controller(self):
        return self._controller.datafile_controller

    def OnCopy(self, event=None):
        self.copy()

    def OnCut(self, event=None):
        self._clipboard_handler.cut()
        self.OnDelete(event)

    def OnDelete(self, event=None):
        if self.IsCellEditControlShown():
            self.delete()
        else:
            self._execute(ClearArea(self.selection.topleft,
                                    self.selection.bottomright))

    def OnPaste(self, event=None):
        if not self.IsCellEditControlShown():
            data = self._clipboard_handler.clipboard_content()
            if data:
                data = [[data]] if isinstance(data, basestring) else data
                self._execute(PasteArea(self.selection.topleft, data))

    def OnDeleteRows(self, event):
        self._execute(DeleteRows(self.selection.rows()))
        event.Skip()

    def OnUndo(self, event=None):
        self._execute(Undo())

    def OnRedo(self, event=None):
        self._execute(Redo())

    def set_dirty(self):
        self._controller.mark_dirty()
        self._tree.mark_dirty(self._controller)

    def close(self):
        self._colorizer.close()
        self.save()
        PUBLISHER.unsubscribe(self._data_changed, RideItemStepsChanged)

    def save(self):
        self._tooltips.hide()
        if self.IsCellEditControlShown():
            cell_editor = self.GetCellEditor(*self.selection.cell)
            cell_editor.EndEdit(self.selection.topleft.row,
                                self.selection.topleft.col, self)

    def show_content_assist(self):
        if self.IsCellEditControlShown():
            self.GetCellEditor(*self.selection.cell).show_content_assist()

    def refresh_datafile(self, item, event):
        self._tree.refresh_datafile(item, event)

    def _calculate_position(self):
        x, y = wx.GetMousePosition()
        return x, y + 20

    def OnEditor(self, event):
        self._tooltips.hide()
        row_height = self.GetRowSize(self.selection.topleft.row)
        self.GetCellEditor(*self.selection.cell).SetHeight(row_height)
        event.Skip()

    def OnKeyDown(self, event):
        keycode, control_down = event.GetKeyCode(), event.CmdDown()
        if keycode == wx.WXK_CONTROL:
            self._show_cell_information()
        elif keycode == ord('A') and control_down:
            self.OnSelectAll(event)
        elif event.AltDown():
            self._move_rows(keycode)
        elif keycode == wx.WXK_WINDOWS_MENU:
            self.OnCellRightClick(event)
        elif control_down or keycode not in [wx.WXK_RETURN, wx.WXK_BACK]:
            if keycode == wx.WXK_SPACE:
                self._open_cell_editor_with_content_assist()
            event.Skip()
        else:
            self._move_grid_cursor(event, keycode)

    def _show_cell_information(self):
        cell = self._cell_under_cursor()
        value = self._cell_value(cell)
        if value:
            self._show_user_keyword_link(cell, value)
            self._show_keyword_details(cell, value)

    def _cell_value(self, cell):
        if cell == self._no_cell:
            return None
        return self.GetCellValue(cell.Row, cell.Col)

    def _show_user_keyword_link(self, cell, value):
        if cell != self._marked_cell and self._plugin.get_user_keyword(value):
            self._toggle_underlined(cell)
            self._marked_cell = cell

    def _show_keyword_details(self, cell, value):
        details = self._plugin.get_keyword_details(value)
        if details:
            self._tooltips.show_info_at(details, value,
                                        self._cell_to_screen_coordinates(cell))

    def _cell_to_screen_coordinates(self, cell):
        point = self.CellToRect(cell.Row, cell.Col).GetTopRight()
        point.x += self.GetRowLabelSize() + 5
        return self.ClientToScreen(self.CalcScrolledPosition(point))

    def _move_rows(self, keycode):
        if keycode == wx.WXK_UP:
            self.OnMoveRowsUp()
        elif keycode == wx.WXK_DOWN:
            self.OnMoveRowsDown()

    def _move_grid_cursor(self, event, keycode):
        self.DisableCellEditControl()
        if keycode == wx.WXK_RETURN:
            self.MoveCursorRight(event.ShiftDown())
        else:
            self.MoveCursorLeft(event.ShiftDown())

    def OnKeyUp(self, event):
        self._tooltips.hide()
        self._hide_link_if_necessary()

    def _open_cell_editor_with_content_assist(self):
        if not self.IsCellEditControlEnabled():
            self.EnableCellEditControl()
        celleditor = self.GetCellEditor(self.GetGridCursorCol(),
                                        self.GetGridCursorRow())
        celleditor.Show(True)
        wx.CallAfter(celleditor.show_content_assist)

    def OnCellRightClick(self, event):
        self._tooltips.hide()
        self._popup_menu_shown = True
        GridEditor.OnCellRightClick(self, event)
        self._popup_menu_shown = False

    def OnSelectAll(self, event):
        self.SelectAll()

    def OnCellLeftClick(self, event):
        self._tooltips.hide()
        if event.ControlDown() or event.CmdDown():
            if self._navigate_to_matching_user_keyword(event.Row, event.Col):
                return
        if not self._has_been_clicked:
            self.SetGridCursor(event.Row, event.Col)
            self._has_been_clicked = True
        else:
            event.Skip()

    def OnCellLeftDClick(self, event):
        self._tooltips.hide()
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

    def _is_active_window(self):
        return self.IsShownOnScreen() and self.FindFocus()

    def _cell_under_cursor(self):
        x, y = self.ScreenToClient(wx.GetMousePosition())
        x -= self.RowLabelSize
        return self.XYToCell(*self.CalcUnscrolledPosition(x, y))

    def _hide_link_if_necessary(self):
        if not self._marked_cell:
            return
        self._toggle_underlined(self._marked_cell)
        self._marked_cell = None

    def OnCreateKeyword(self, event):
        cmd = AddKeywordFromCells(self._data_cells_from_current_row())
        try:
            self._execute(cmd)
        except ValueError, err:
            wx.MessageBox(unicode(err))

    def _data_cells_from_current_row(self):
        currow, curcol = self.selection.cell
        rowdata = self._row_data(currow)[curcol:]
        return self._strip_trailing_empty_cells(self._remove_comments(rowdata))

    def _remove_comments(self, data):
        for index, cell in enumerate(data):
            if cell.strip().startswith('#'):
                return data[:index]
        return data

    def OnExtractKeyword(self, event):
        dlg = UserKeywordNameDialog(self._controller)
        if dlg.ShowModal() == wx.ID_OK:
            name, args = dlg.get_value()
            rows = self.selection.topleft.row, self.selection.bottomright.row
            self._execute(ExtractKeyword(name, args, rows))

    def OnExtractVariable(self, event):
        cells = self.selection.cells()
        if len(cells) == 1:
            self._extract_scalar(cells[0])
        elif min(row for row, _ in cells) == max(row for row, _ in cells):
            self._extract_list(cells)

    def _extract_scalar(self, cell):
        var = Variable('', self.GetCellValue(*cell), '')
        dlg = ScalarVariableDialog(self._controller.datafile_controller.variables, var)
        if dlg.ShowModal() == wx.ID_OK:
            name, value = dlg.get_value()
            comment = dlg.get_comment()
            self._execute(ExtractScalar(name, value, comment, cell))

    def _extract_list(self, cells):
        var = Variable('', [self.GetCellValue(*cell) for cell in cells], '')
        dlg = ListVariableDialog(self._controller.datafile_controller.variables, var)
        if dlg.ShowModal() == wx.ID_OK:
            name, value = dlg.get_value()
            comment = dlg.get_comment()
            self._execute(ExtractList(name, value, comment, cells))

    def OnRenameKeyword(self, event):
        old_name = self._current_cell_value()
        if not old_name.strip():
            return
        new_name = wx.GetTextFromUser('New name', 'Rename Keyword',
                                      default_value=old_name)
        if new_name:
            self._execute(RenameKeywordOccurrences(old_name, new_name))


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
        value = self._get_value()
        if value != self._original_value:
            grid.cell_value_edited(row, col, value)
        self._tc.hide()
        grid.SetFocus()
        return True

    def _get_value(self):
        suggestion = self._tc.content_assist_value()
        return suggestion or self._tc.GetValue()

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
