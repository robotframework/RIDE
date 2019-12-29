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
from wx import grid
import json
from robotide.editor.cellrenderer import CellRenderer
from robotide import context

if wx.VERSION >= (3, 0, 3, ''):  # DEBUG wxPhoenix
    from wx.grid import GridCellEditor
    # import sys
    # sys.setrecursionlimit(200)  # with 150 crashes at edit cell
else:
    from wx.grid import PyGridCellEditor as GridCellEditor

from robotide.context import IS_MAC, IS_WINDOWS
from robotide.controller.ctrlcommands import ChangeCellValue, ClearArea, \
    PasteArea, DeleteRows, AddRows, CommentRows, InsertCells, DeleteCells, \
    UncommentRows, Undo, Redo, RenameKeywordOccurrences, ExtractKeyword, \
    AddKeywordFromCells, MoveRowsUp, MoveRowsDown, ExtractScalar, ExtractList, \
    InsertArea
from robotide.controller.cellinfo import TipMessage, ContentType, CellType
from robotide.publish import (RideItemStepsChanged, RideSaved,
                              RideSettingsChanged, PUBLISHER)
from robotide.usages.UsageRunner import Usages, VariableUsages
from robotide.ui.progress import RenameProgressObserver
from robotide import robotapi, utils
from robotide.utils import RideEventHandler, variablematcher
from robotide.widgets import Dialog, PopupMenu, PopupMenuItems

from .gridbase import GridEditor
from .tooltips import GridToolTips
from .editordialogs import UserKeywordNameDialog, ScalarVariableDialog, \
    ListVariableDialog
from .contentassist import ExpandingContentAssistTextCtrl
from .gridcolorizer import Colorizer
from robotide.utils import PY3
from robotide.lib.robot.utils.compat import with_metaclass

if PY3:
    from robotide.utils import basestring, unicode, unichr

_DEFAULT_FONT_SIZE = 11


def requires_focus(function):
    def _row_header_selected_on_linux(self):
        # print("DEBUG: _row_header_selected_on_linux: %s has focus %s\n" % (self.FindFocus(), self.has_focus()))
        return self.FindFocus() is None  # or isinstance(GridEditor)

    def decorated_function(self, *args):
        # if wx.VERSION >= (3, 0, 3, ''):  # DEBUG wxPhoenix
        #     _iscelleditcontrolshown = self.IsCellEditControlEnabled()
        # else:
        #     _iscelleditcontrolshown = self.IsCellEditControlShown()
        if not self.has_focus():
            return
        _iscelleditcontrolshown = self.IsCellEditControlShown()
        # print("DEBUG: decorated: iscelleditshown = %s focus =%s rowheaderselected=%s\n" % (_iscelleditcontrolshown, self.has_focus(), _row_header_selected_on_linux(self)))
        if self.has_focus() or _iscelleditcontrolshown or \
                _row_header_selected_on_linux(self):
            function(self, *args)

    return decorated_function


# Metaclass fix from http://code.activestate.com/recipes/204197-solving-the-metaclass-conflict/
from robotide.utils.noconflict import classmaker


class KeywordEditor(with_metaclass(classmaker(), GridEditor, RideEventHandler)):
    _no_cell = (-1, -1)
    _popup_menu_shown = False
    dirty = property(lambda self: self._controller.dirty)
    update_value = lambda *args: None
    _popup_items = [
                       'Create Keyword', 'Extract Keyword', 'Extract Variable',
                       'Rename Keyword', 'Find Where Used',
                       'JSON Editor\tCtrl-Shift-J',
                       '---', 'Make Variable\tCtrl-1',
                       'Make List Variable\tCtrl-2',
                       'Make Dict Variable\tCtrl-5', '---',
                       'Go to Definition\tCtrl-B', '---'
                   ] + GridEditor._popup_items

    def __init__(self, parent, controller, tree):
        GridEditor.__init__(
            self, parent, len(controller.steps) + 5,
            max((controller.max_columns + 1), 5),
            parent.plugin._grid_popup_creator)

        self.settings = parent.plugin.global_settings['Grid']
        self._parent = parent
        self._plugin = parent.plugin
        self._cell_selected = False
        self._colorizer = Colorizer(self, controller)
        self._controller = controller
        self._configure_grid()
        self._updating_namespace = False
        self._controller.datafile_controller.register_for_namespace_updates(
            self._namespace_updated)
        self._tooltips = GridToolTips(self)
        self._marked_cell = None
        self._make_bindings()
        self._write_steps(self._controller)
        self.autosize()
        self._tree = tree
        self._has_been_clicked = False
        self._counter = 0  # Workaround for double delete actions
        self._dcells = None  # Workaround for double delete actions
        self._icells = None  # Workaround for double insert actions
        PUBLISHER.subscribe(self._data_changed, RideItemStepsChanged)
        PUBLISHER.subscribe(self.OnSettingsChanged, RideSettingsChanged)
        PUBLISHER.subscribe(self._resize_grid, RideSaved)

    def _namespace_updated(self):
        if not self._updating_namespace:
            self._updating_namespace = True
            # See following issue for history of the next line:
            # http://code.google.com/p/robotframework-ride/issues/detail?id=1108
            wx.CallAfter(
                wx.CallLater, 200, self._update_based_on_namespace_change)

    def _update_based_on_namespace_change(self):
        try:
            self._colorize_grid()
        finally:
            self._updating_namespace = False

    @requires_focus
    def _resize_grid(self, event=None):
        if self.settings.get("auto size cols", True):
            self.AutoSizeColumns(False)
        if self.settings.get("word wrap", True):
            self.AutoSizeRows(False)

    def _set_cells(self):
        col_size = self.settings.get("col size", 150)
        max_col_size = self.settings.get("max col size", 450)
        auto_col_size = self.settings.get("auto size cols", False)
        word_wrap = self.settings.get("word wrap", True)

        self.SetDefaultRenderer(
            CellRenderer(col_size, max_col_size, auto_col_size, word_wrap))
        self.SetRowLabelSize(wx.grid.GRID_AUTOSIZE)
        self.SetColLabelSize(0)

        if auto_col_size:
            self.SetDefaultColSize(wx.grid.GRID_AUTOSIZE, resizeExistingCols=True)
        else:
            self.SetDefaultColSize(col_size, resizeExistingCols=True)
            self.SetColMinimalAcceptableWidth(col_size)

        if auto_col_size:
            self.Bind(grid.EVT_GRID_CMD_COL_SIZE, self.OnCellColSizeChanged)
        else:
            self.Unbind(grid.EVT_GRID_CMD_COL_SIZE)

        if word_wrap:
            self.SetDefaultRowSize(wx.grid.GRID_AUTOSIZE)
        self.SetDefaultCellOverflow(False)  # DEBUG

    def _configure_grid(self):
        self._set_cells()
        self.SetDefaultEditor(
            ContentAssistCellEditor(self._plugin, self._controller))
        self._set_fonts()

    def _set_fonts(self, update_cells=False):
        font_size = self.settings.get('font size', _DEFAULT_FONT_SIZE)
        font_family = wx.FONTFAMILY_MODERN if self.settings['fixed font'] \
            else wx.FONTFAMILY_DEFAULT
        font_face = self.settings.get('font face', None)
        if font_face is None:
            font = wx.Font(font_size, font_family, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
            self.settings.set('font face', font.GetFaceName())
        else:
            font = wx.Font(font_size, font_family, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, font_face)
        self.SetDefaultCellFont(font)
        for row in range(self.NumberRows):
            for col in range(self.NumberCols):
                self.SetCellFont(row, col, font)
                self.ForceRefresh()

    def _make_bindings(self):
        self.Bind(grid.EVT_GRID_EDITOR_SHOWN, self.OnEditor)
        self.Bind(wx.EVT_KEY_DOWN, self.OnKeyDown)
        self.Bind(wx.EVT_KEY_UP, self.OnKeyUp)
        self.Bind(grid.EVT_GRID_CELL_LEFT_CLICK, self.OnCellLeftClick)
        self.Bind(grid.EVT_GRID_CELL_LEFT_DCLICK, self.OnCellLeftDClick)
        self.Bind(grid.EVT_GRID_LABEL_RIGHT_CLICK, self.OnLabelRightClick)
        self.Bind(grid.EVT_GRID_LABEL_LEFT_CLICK, self.OnLabelLeftClick)
        self.Bind(wx.EVT_KILL_FOCUS, self.OnKillFocus)

    def get_tooltip_content(self):
        """ Fixed on 4.0.0a3
        if wx.VERSION >= (3, 0, 3, ''):  # DEBUG wxPhoenix
            _iscelleditcontrolshown = self.IsCellEditControlEnabled()
        else:
        """
        _iscelleditcontrolshown = self.IsCellEditControlShown()
        if _iscelleditcontrolshown or self._popup_menu_shown:
            return ''
        cell = self.cell_under_cursor
        cell_info = self._controller.get_cell_info(cell.Row, cell.Col)
        return TipMessage(cell_info)

    def OnSettingsChanged(self, data):
        '''Redraw the colors if the color settings are modified'''
        section, setting = data.keys
        if section == 'Grid':
            if 'font' in setting:
                self._set_fonts(update_cells=True)
            elif ('col size' in setting
                  or 'max col size' in setting
                  or 'auto size cols' in setting
                  or 'word wrap' in setting):
                self._set_cells()
            self.autosize()
            self._colorize_grid()

    def OnSelectCell(self, event):
        self._cell_selected = True
        GridEditor.OnSelectCell(self, event)
        self._colorize_grid()
        event.Skip()

    def OnKillFocus(self, event):
        self._tooltips.hide()
        self._hide_link_if_necessary()
        self.save()
        event.Skip()

    def _execute(self, command):
        return self._controller.execute(command)

    def _toggle_underlined(self, cell):
        font = self.GetCellFont(cell.Row, cell.Col)
        font.SetUnderlined(not font.Underlined)
        self.SetCellFont(cell.Row, cell.Col, font)
        self.Refresh()

    def OnLabelRightClick(self, event):
        if event.Col == -1:
            self._row_label_right_click(event)
        else:
            self._col_label_right_click(event)

    def _row_label_right_click(self, event):
        selected_row = event.GetRow()
        selected_rows = self.selection.rows()
        if selected_row not in selected_rows:
            self.SelectRow(selected_row, addToSelected=False)
            self.SetGridCursor(event.Row, 0)
        popupitems = ['Insert Rows\tCtrl-I', 'Delete Rows\tCtrl-D',
                      'Comment Rows\tCtrl-3', 'Uncomment Rows\tCtrl-4',
                      'Move Rows Up\tAlt-Up', 'Move Rows Down\tAlt-Down']
        PopupMenu(self, PopupMenuItems(self, popupitems))
        event.Skip()

    def _col_label_right_click(self, event):
        pass

    def OnLabelLeftClick(self, event):
        if event.Col == -1:
            self._row_label_left_click(event)
        else:
            self._col_label_left_click(event)

    def _row_label_left_click(self, event):
        if event.ShiftDown() or event.ControlDown():
            self.ClearSelection()
            cursor_row = self.GetGridCursorRow()
            event_row = event.Row
            start, end = (cursor_row, event_row) \
                if cursor_row < event_row else (event_row, cursor_row)
            for row in range(start, end + 1):
                self.SelectRow(row, addToSelected=True)
        else:
            self.SelectRow(event.Row, addToSelected=False)
            self.SetGridCursor(event.Row, 0)

    def _col_label_left_click(self, event):
        pass

    def OnInsertRows(self, event):
        self._execute(AddRows(self.selection.rows()))
        self.ClearSelection()
        self._resize_grid()
        self._skip_except_on_mac(event)

    def _skip_except_on_mac(self, event):  # TODO Do we still need this?
        if event is not None and not IS_MAC:
            # print("DEBUG skip!")
            event.Skip()

    def OnInsertCells(self, event=None):
        # TODO remove below workaround for double actions
        if self._counter == 1:
            if self._icells == (
                    self.selection.topleft, self.selection.bottomright):
                self._counter = 0
                self._icells = None
                return
        else:
            self._counter = 1

        self._icells = (self.selection.topleft,
                        self.selection.bottomright)
        self._execute(InsertCells(self.selection.topleft,
                                  self.selection.bottomright))
        self._resize_grid()
        self._skip_except_on_mac(event)

    def OnDeleteCells(self, event=None):
        # TODO remove below workaround for double actions
        if self._counter == 1:
            if self._dcells == (self.selection.topleft,
                                self.selection.bottomright):
                self._counter = 0
                self._dcells = None
                return
        else:
            self._counter = 1

        self._dcells = (self.selection.topleft,
                        self.selection.bottomright)
        # print("DEBUG kweditor delete cells %s, %s " % (self.selection.topleft,
        #                          self.selection.bottomright))
        self._execute(DeleteCells(self.selection.topleft,
                                  self.selection.bottomright))
        self._resize_grid()
        self._skip_except_on_mac(event)

    # DEBUG @requires_focus
    def OnCommentRows(self, event=None):
        self._execute(CommentRows(self.selection.rows()))
        self._resize_grid()
        self._skip_except_on_mac(event)

    # DEBUG @requires_focus
    def OnUncommentRows(self, event=None):
        self._execute(UncommentRows(self.selection.rows()))
        self._resize_grid()
        self._skip_except_on_mac(event)

    def OnMoveRowsUp(self, event=None):
        self._row_move(MoveRowsUp, -1)

    def OnMoveRowsDown(self, event=None):
        self._row_move(MoveRowsDown, 1)

    def _row_move(self, command, change):
        # Workaround for double actions, see issue #2048
        if self._counter == 1:
            if IS_MAC:
                row=self.GetGridCursorRow() + change
                col=self.GetGridCursorCol()
                if row >= 0:
                    self.SetGridCursor(row, col)
                self._counter = 0
                return
        else:
            self._counter += 1
        rows = self.selection.rows()
        if self._execute(command(rows)):
            wx.CallAfter(self._select_rows, [r + change for r in rows])
        self._resize_grid()

    def _select_rows(self, rows):
        self.ClearSelection()
        for r in rows:
            self.SelectRow(r, True)

    def OnMotion(self, event):
        pass

    def _data_changed(self, data):
        if self._controller == data.item:
            self._write_steps(data.item)

    def _write_steps(self, controller):
        data = []
        self._write_headers(controller)
        for step in controller.steps:
            data.append(self._format_comments(step.as_list()))
        self.ClearGrid()
        self._write_data(data, update_history=False)
        self._colorize_grid()

    def _write_headers(self, controller):
        headers = controller.data.parent.header[1:]
        if not headers:
            self.SetColLabelSize(0)
            return
        self.SetColLabelSize(wx.grid.GRID_AUTOSIZE)  # DEBUG
        for col, header in enumerate(headers):
            self.SetColLabelValue(col, header)
        for empty_col in range(col + 1, self.NumberCols + 1):
            self.SetColLabelValue(empty_col, '')

    def _colorize_grid(self):
        selection_content = \
            self._get_single_selection_content_or_none_on_first_call()
        if selection_content is None:
            self.highlight(None)
        else:
            self._parent.highlight(selection_content, expand=False)

    def highlight(self, text, expand=True):
        # Below CallAfter was causing C++ assertions(objects not found)
        # When calling Preferences Grid Colors change
        wx.CallLater(100, self._colorizer.colorize, text)

    def autosize(self):
        wx.CallAfter(self.AutoSizeColumns, False)
        wx.CallAfter(self.AutoSizeRows, False)

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
        wx.CallAfter(self.AutoSizeColumn, col, False)
        wx.CallAfter(self.AutoSizeRow, row, False)

    def get_selected_datafile_controller(self):
        return self._controller.datafile_controller

    # DEBUG @requires_focus
    def OnCopy(self, event=None):
        # print("DEBUG: OnCopy called event %s\n" % str(event))
        self.copy()

    # DEBUG @requires_focus
    def OnCut(self, event=None):
        self._clipboard_handler.cut()
        self.OnDelete(event)

    def OnDelete(self, event=None):
        """ Fixed on 4.0.0a3
        if wx.VERSION >= (3, 0, 3, ''):  # DEBUG wxPhoenix
            _iscelleditcontrolshown = self.IsCellEditControlEnabled()
        else:
        """
        _iscelleditcontrolshown = self.IsCellEditControlShown()
        if _iscelleditcontrolshown:  # TODO Review if still needed
            # On Windows, Delete key does not work in TextCtrl automatically
            self.delete()
        elif self.has_focus():
            self._execute(ClearArea(self.selection.topleft,
                                    self.selection.bottomright))
        self._resize_grid()

    # DEBUG    @requires_focus
    def OnPaste(self, event=None):
        self._execute_clipboard_command(PasteArea)
        self._resize_grid()

    def _execute_clipboard_command(self, command_class):
        """ Fixed on 4.0.0a3
        if wx.VERSION >= (3, 0, 3, ''):  # DEBUG wxPhoenix
            _iscelleditcontrolshown = self.IsCellEditControlEnabled()
        else:
        """
        _iscelleditcontrolshown = self.IsCellEditControlShown()
        if not _iscelleditcontrolshown:
            data = self._clipboard_handler.clipboard_content()
            if data:
                data = [[data]] if isinstance(data, basestring) else data
                self._execute(command_class(self.selection.topleft, data))

    # DEBUG @requires_focus
    def OnInsert(self, event=None):
        self._execute_clipboard_command(InsertArea)
        self._resize_grid()

    def OnDeleteRows(self, event):
        self._execute(DeleteRows(self.selection.rows()))
        self.ClearSelection()
        self._resize_grid()
        self._skip_except_on_mac(event)

    # DEBUG @requires_focus
    def OnUndo(self, event=None):
        """ Fixed on 4.0.0a3
        if wx.VERSION >= (3, 0, 3, ''):  # DEBUG wxPhoenix
            _iscelleditcontrolshown = self.IsCellEditControlEnabled()
        else:
        """
        _iscelleditcontrolshown = self.IsCellEditControlShown()
        if not _iscelleditcontrolshown:
            self._execute(Undo())
        else:
            self.GetCellEditor(*self.selection.cell).Reset()
        self._resize_grid()

    # DEBUG @requires_focus
    def OnRedo(self, event=None):
        self._execute(Redo())
        self._resize_grid()

    def close(self):
        self._colorizer.close()
        self.save()
        PUBLISHER.unsubscribe(self._data_changed, RideItemStepsChanged)
        if self._namespace_updated:
            # Prevent re-entry to unregister method
            self._controller.datafile_controller.unregister_namespace_updates(
                self._namespace_updated)
        self._namespace_updated = None

    def save(self):
        self._tooltips.hide()
        """ Fixed on 4.0.0a3
        if wx.VERSION >= (3, 0, 3, ''):  # DEBUG wxPhoenix
            _iscelleditcontrolshown = self.IsCellEditControlEnabled()
        else:
        """
        _iscelleditcontrolshown = self.IsCellEditControlShown()
        if _iscelleditcontrolshown:
            cell_editor = self.GetCellEditor(*self.selection.cell)
            cell_editor.EndEdit(self.selection.topleft.row,
                                self.selection.topleft.col, self)

    def show_content_assist(self):
        """ Fixed on 4.0.0a3
        if wx.VERSION >= (3, 0, 3, ''):  # DEBUG wxPhoenix
            _iscelleditcontrolshown = self.IsCellEditControlEnabled()
        else:
        """
        _iscelleditcontrolshown = self.IsCellEditControlShown()
        if _iscelleditcontrolshown:
            self.GetCellEditor(*self.selection.cell).show_content_assist(
                self.selection.cell)  # DEBUG self.selection.topleft.row)

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

    def _move_cursor_down(self, event):
        self.DisableCellEditControl()
        self.MoveCursorDown(event.ShiftDown())

    def OnKeyDown(self, event):
        """ Fixed on 4.0.0a3
        if wx.VERSION >= (3, 0, 3, ''):  # DEBUG wxPhoenix
            _iscelleditcontrolshown = self.IsCellEditControlEnabled()
        else:
        """
        _iscelleditcontrolshown = self.IsCellEditControlShown()

        keycode, control_down = event.GetKeyCode(), event.ControlDown()
        # print("DEBUG: key pressed " + str(keycode) + " + " +  str(control_down))
        # event.Skip()  # DEBUG seen this skip as soon as possible
        if keycode != wx.WXK_SPACE and control_down:  # keycode == wx.WXK_CONTROL  or event.AltDown()
            self.show_cell_information()
        elif keycode == wx.WXK_SPACE and (control_down or event.AltDown()):  # Avoid Mac CMD
            self._open_cell_editor_with_content_assist()
        elif keycode == ord('C') and control_down:
            # print("DEBUG: captured Control-C\n")
            self.OnCopy(event)
        elif keycode == ord('X') and control_down:
            self.OnCut(event)
        elif keycode == ord('V') and control_down:
            self.OnPaste(event)
        elif keycode == ord('Z') and control_down:
            self.OnUndo(event)
        elif keycode == ord('A') and control_down:
            self.OnSelectAll(event)
        elif keycode == ord('F') and control_down:
            # print("DEBUG: captured Control-F\n")
            if not self.has_focus():
                self.SetFocus()  # DEBUG Avoiding Search field on Text Edit
        elif event.AltDown() and keycode in [wx.WXK_DOWN, wx.WXK_UP]:
            # print("DEBUG: Alt-Move %s" % self._counter)
            self._skip_except_on_mac(event)
            self._move_rows(keycode)
        elif event.AltDown() and keycode == wx.WXK_RETURN:
            self._move_cursor_down(event)
            # event.Skip()
        elif keycode == wx.WXK_WINDOWS_MENU:
            self.OnCellRightClick(event)
        elif keycode in [wx.WXK_RETURN, wx.WXK_BACK]:
            if _iscelleditcontrolshown:
                self.save()
            self._move_grid_cursor(event, keycode)
            # event.Skip()
        elif control_down and not event.AltDown() and \
                keycode in (ord('1'), ord('2'), ord('5')):
            self._open_cell_editor_and_execute_variable_creator(
                list_variable=(keycode == ord('2')),
                dict_variable=(keycode == ord('5')))
        elif control_down and event.ShiftDown() and keycode == ord('I'):
            self.OnInsertCells()
        elif control_down and event.ShiftDown() and keycode == ord('J'):
            self.OnJsonEditor(event)
        elif control_down and event.ShiftDown() and keycode == ord('D'):
            self.OnDeleteCells()
        elif control_down and keycode == ord('B'):
            self._navigate_to_matching_user_keyword(
                self.GetGridCursorRow(), self.GetGridCursorCol())
        else:
            event.Skip()

    def OnGoToDefinition(self, event):
        self._navigate_to_matching_user_keyword(
            self.GetGridCursorRow(), self.GetGridCursorCol())

    def show_cell_information(self):
        cell = self.cell_under_cursor
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
        if not details:
            info = self._controller.get_cell_info(cell.Row, cell.Col)
            if info.cell_type == CellType.KEYWORD and info.content_type == \
                    ContentType.STRING:
                details = """\
        <b>Keyword was not detected by RIDE</b>
        <br>Possible corrections:<br>
        <ul>
            <li>Import library or resource file containing the keyword.</li>
            <li>For library import errors: Consider importing library spec XML
            (Tools / Import Library Spec XML or by adding the XML file with the
            correct name to PYTHONPATH) to enable keyword completion
            for example for Java libraries.
            Library spec XML can be created using libdoc tool from Robot Frame\
work.</li>
        </ul>"""
        if details:
            self._tooltips.show_info_at(
                details, value, self._cell_to_screen_coordinates(cell))

    def _cell_to_screen_coordinates(self, cell):
        point = self.CellToRect(cell.Row, cell.Col).GetTopRight()
        point.x += self.GetRowLabelSize() + 5
        return self.ClientToScreen(self.CalcScrolledPosition(point))

    def _move_rows(self, keycode):
        if keycode == wx.WXK_UP:
            self.OnMoveRowsUp()
        else:
            self.OnMoveRowsDown()

    def _move_grid_cursor(self, event, keycode):
        self.DisableCellEditControl()
        if keycode == wx.WXK_RETURN:
            self.MoveCursorRight(event.ShiftDown())
        else:
            self.MoveCursorLeft(event.ShiftDown())

    def OnKeyUp(self, event):
        event.Skip()  # DEBUG seen this skip as soon as possible
        self._tooltips.hide()
        self._hide_link_if_necessary()
        #  event.Skip()

    def _open_cell_editor_with_content_assist(self):
        if not self.IsCellEditControlEnabled():
            self.EnableCellEditControl()
        row = self.GetGridCursorRow()
        celleditor = self.GetCellEditor(self.GetGridCursorCol(), row)
        celleditor.Show(True)
        wx.CallAfter(celleditor.show_content_assist)

    def _open_cell_editor_and_execute_variable_creator(
            self, list_variable=False, dict_variable=False):
        if not self.IsCellEditControlEnabled():
            self.EnableCellEditControl()
        row = self.GetGridCursorRow()
        celleditor = self.GetCellEditor(self.GetGridCursorCol(), row)
        celleditor.Show(True)
        wx.CallAfter(celleditor.execute_variable_creator, list_variable,
                     dict_variable)

    def OnMakeVariable(self, event):
        self._open_cell_editor_and_execute_variable_creator(
            list_variable=False)

    def OnMakeListVariable(self, event):
        self._open_cell_editor_and_execute_variable_creator(list_variable=True)

    def OnMakeDictVariable(self, event):
        self._open_cell_editor_and_execute_variable_creator(dict_variable=True)

    def OnCellRightClick(self, event):
        self._tooltips.hide()
        self._popup_menu_shown = True
        GridEditor.OnCellRightClick(self, event)
        self._popup_menu_shown = False

    def OnSelectAll(self, event):
        self.SelectAll()

    def OnCellColSizeChanged(self, event):
        wx.CallAfter(self.AutoSizeRows, False)
        event.Skip()

    def OnCellLeftClick(self, event):
        self._tooltips.hide()
        # if event.GetModifiers() == wx.MOD_CONTROL:
        #  or event.CmdDown(): # DEBUG wxPhoenix
        if event.ControlDown():
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
            wx.CallAfter(self._tree.select_user_keyword_node, uk)
            return True
        return False

    def _is_active_window(self):
        return self.IsShownOnScreen() and self.FindFocus()

    def _hide_link_if_necessary(self):
        if not self._marked_cell:
            return
        self._toggle_underlined(self._marked_cell)
        self._marked_cell = None

    def OnCreateKeyword(self, event):
        cells = self._data_cells_from_current_row()
        if not cells:
            return
        try:
            self._execute(AddKeywordFromCells(cells))
        except ValueError as err:
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
        self._resize_grid()

    def OnFindWhereUsed(self, event):
        is_variable, searchstring = self._get_is_variable_and_searchstring()
        if searchstring:
            self._execute_find_where_used(is_variable, searchstring)

    def _get_is_variable_and_searchstring(self):
        cellvalue = self.GetCellValue(*self.selection.cells()[0])
        if self._cell_value_contains_multiple_search_items(cellvalue):
            choice_dialog = ChooseUsageSearchStringDialog(cellvalue)
            choice_dialog.ShowModal()
            is_var, value = choice_dialog.GetStringSelection()
            choice_dialog.Destroy()
            return is_var, value
        else:
            return variablematcher.is_variable(cellvalue), cellvalue

    def _execute_find_where_used(self, is_variable, searchstring):
        usages_dialog_class = VariableUsages if is_variable else Usages
        usages_dialog_class(
            self._controller,
            self._tree.highlight, searchstring).show()

    def _cell_value_contains_multiple_search_items(self, value):
        variables = variablematcher.find_variable_basenames(value)
        return variables and variables[0] != value

    def _extract_scalar(self, cell):
        var = robotapi.Variable(
            self._controller.datafile.variable_table, '',
            self.GetCellValue(*cell), '')
        dlg = ScalarVariableDialog(
            self._controller.datafile_controller.variables, var)
        if dlg.ShowModal() == wx.ID_OK:
            name, value = dlg.get_value()
            comment = dlg.get_comment()
            self._execute(ExtractScalar(name, value, comment, cell))

    def _extract_list(self, cells):
        var = robotapi.Variable(
            self._controller.datafile.variable_table,
            '', [self.GetCellValue(*cell) for cell in cells], '')
        dlg = ListVariableDialog(
            self._controller.datafile_controller.variables, var, self._plugin)
        if dlg.ShowModal() == wx.ID_OK:
            name, value = dlg.get_value()
            comment = dlg.get_comment()
            self._execute(ExtractList(name, value, comment, cells))

    def OnRenameKeyword(self, event):
        old_name = self._current_cell_value()
        if not old_name.strip() or variablematcher.is_variable(old_name):
            return
        new_name = wx.GetTextFromUser('New name', 'Rename Keyword',
                                      default_value=old_name)
        if new_name:
            self._execute(RenameKeywordOccurrences(
                old_name, new_name, RenameProgressObserver(self.GetParent())))

    # Add one new Dialog to edit pretty json String
    def OnJsonEditor(self, event=None):
        if event:
            event.Skip()
        dialog = Dialog()
        dialog.SetTitle('JSON Editor')
        dialog.SetSizer(wx.BoxSizer(wx.HORIZONTAL))
        okBtn = wx.Button(dialog, wx.ID_OK, "Save")
        cnlBtn = wx.Button(dialog, wx.ID_CANCEL, "Cancel")
        richText = wx.TextCtrl(dialog, wx.ID_ANY, "If supported by the native "
                                                  "control, this is reversed, "
                                                  "and this is a different "
                                                  "font.",
                               size=(400, 475),
                               style=wx.HSCROLL | wx.TE_MULTILINE)
        dialog.Sizer.Add(richText, flag=wx.GROW, proportion=1)
        dialog.Sizer.Add(okBtn, flag=wx.ALIGN_RIGHT | wx.ALL)
        dialog.Sizer.Add(cnlBtn, flag=wx.ALL)
        # Get cell value of parent grid
        if self.is_json(self._current_cell_value()):
            jsonStr = json.loads(self._current_cell_value())
            richText.SetValue(
                json.dumps(jsonStr, indent=4, ensure_ascii=False))
        else:
            richText.SetValue(self._current_cell_value())
        dialog.SetSize((650, 550))
        # If click Save, then save the value in richText into the original
        # grid cell, and clear all indent.
        if dialog.ShowModal() == wx.ID_OK:
            try:
                strJson = json.loads(richText.GetValue())
                self.cell_value_edited(self.selection.cell[0],
                                       self.selection.cell[1],
                                       json.dumps(strJson,
                                                  ensure_ascii=False))
            except ValueError or json.JSONDecodeError as e:
                res = wx.MessageDialog(dialog,
                                       "Error in JSON: {}\n\n"
                                       "Save anyway?".format(e),
                                       "Validation Error!",
                                       wx.YES_NO).ShowModal()
                if res == wx.ID_YES:
                    self.cell_value_edited(self.selection.cell[0],
                                           self.selection.cell[1],
                                           richText.GetValue())
                else:
                    pass

    # If the jsonStr is json format, then return True
    def is_json(self, jsonStr):
        try:
            json.loads(jsonStr)
        except ValueError:
            return False
        return True


class ContentAssistCellEditor(GridCellEditor):  # DEBUG wxPhoenix PyGridCellEdi

    def __init__(self, plugin, controller):
        GridCellEditor.__init__(self)
        self._plugin = plugin
        self._controller = controller
        self._grid = None
        self._original_value = None
        self._value = None
        self._tc = None
        self._counter = 0

    def show_content_assist(self, args=None):
        if self._tc:
            self._tc.show_content_assist()

    def execute_variable_creator(self, list_variable=False,
                                 dict_variable=False):
        self._tc.execute_variable_creator(list_variable, dict_variable)

    def Create(self, parent, id, evthandler):
        self._tc = ExpandingContentAssistTextCtrl(
            parent, self._plugin, self._controller)
        self.SetControl(self._tc)
        if evthandler:
            self._tc.PushEventHandler(evthandler)

    def SetSize(self, rect):
        if wx.VERSION >= (3, 0, 3, ''):  # DEBUG wxPhoenix
            self._tc.SetSize(rect.x, rect.y, rect.width + 2, rect.height + 2,
                             wx.SIZE_ALLOW_MINUS_ONE)
        else:
            self._tc.SetDimensions(rect.x, rect.y, rect.width + 2, rect.height
                                   + 2, wx.SIZE_ALLOW_MINUS_ONE)

    def SetHeight(self, height):
        self._height = height

    def BeginEdit(self, row, col, grid):
        self._counter = 0
        self._tc.SetSize((-1, self._height))
        self._tc.SetBackgroundColour(context.POPUP_BACKGROUND)  # DEBUG: We are now in Edit mode
        self._tc.set_row(row)
        self._original_value = grid.GetCellValue(row, col)
        self._tc.SetValue(self._original_value)
        self._grid = grid
        self._tc.SetInsertionPointEnd()
        if not IS_WINDOWS:
            self._tc.SetFocus()  # On Win 10 this breaks cell text selection
        # For this example, select the text   # DEBUG nov_2017
        # self._tc.SetSelection(0, self._tc.GetLastPosition())

    def EndEdit(self, row, col, grid, *ignored):
        value = self._get_value()
        if value != self._original_value:
            if wx.VERSION >= (3, 0, 2, ''):  # DEBUG wxPhoenix
                self._value = value
                return value  # DEBUG wxPhoenix True
            else:
                self._grid.cell_value_edited(row, col, value)
                return True  # DEBUG wxPhoenix True
        else:
            # DEBUG wxPhoenix
            self._tc.hide()
            grid.SetFocus()
        """    if wx.VERSION >= (3, 0, 2, ''):  # DEBUG wxPhoenix
                return None
            else:
                return None   # DEBUG
        """

    def ApplyEdit(self, row, col, grid):
        val = self._tc.GetValue()
        grid.GetTable().SetValue(row, col, val)  # update the table

        self._original_value = ''
        self._tc.SetValue('')
        if wx.VERSION >= (3, 0, 2, ''):  # DEBUG wxPhoenix
            if self._value and val != '':  # DEBUG Fix #1967 crash when click other cell
                self._grid.cell_value_edited(row, col, self._value)
            else:
                self._tc.hide()

    def _get_value(self):
        suggestion = self._tc.content_assist_value()
        return suggestion or self._tc.GetValue()

    def Reset(self):
        self._tc.SetValue(self._original_value)
        self._tc.reset()

    def StartingKey(self, event):
        key = event.GetKeyCode()
        event.Skip()  # DEBUG seen this skip as soon as possible
        if key == wx.WXK_DELETE or key > 255:
            self._grid.HideCellEditControl()
        elif key == wx.WXK_BACK:
            self._tc.SetValue(self._original_value)
        else:
            self._tc.SetValue(unichr(key))
        self._tc.SetFocus()
        self._tc.SetInsertionPointEnd()

    def StartingClick(self):
        self._tc.SetValue(self._original_value)
        self._tc.SelectAll()
        self._tc.SetFocus()

    def Clone(self):
        return ContentAssistCellEditor()


class ChooseUsageSearchStringDialog(wx.Dialog):

    def __init__(self, cellvalue):
        wx.Dialog.__init__(self, None, wx.ID_ANY, "Find Where Used",
                           style=wx.DEFAULT_DIALOG_STYLE)
        self.caption = "Please select what you want to check for usage"
        variables = set(variablematcher.find_variable_basenames(cellvalue))
        self.choices = [(False, cellvalue)] + [(True, v) for v in variables]
        self.choices_string = ["Complete cell content"] + \
                              ["Variable " + var.replace("&", "&&") for var
                               in variables]
        self._build_ui()

    def _build_ui(self):
        self.radiobox_choices = wx.RadioBox(
            self, choices=self.choices_string, style=wx.RA_SPECIFY_COLS,
            majorDimension=1)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(wx.StaticText(self, label=self.caption), 0, wx.ALL |
                  wx.EXPAND, 5)
        sizer.Add(self.radiobox_choices, 0, wx.ALL | wx.EXPAND, 5)
        sizer.Add(wx.Button(self, wx.ID_OK, label="Search"),
                  0, wx.ALL | wx.ALIGN_CENTER, 5)
        big_sizer = wx.BoxSizer(wx.VERTICAL)
        big_sizer.Add(sizer, 0, wx.ALL, 10)
        self.SetSizer(big_sizer)
        self.Fit()
        self.CenterOnParent()

    def GetStringSelection(self):
        return self.choices[self.radiobox_choices.GetSelection()]
