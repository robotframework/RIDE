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

import json
from json.decoder import JSONDecodeError

import wx
from wx import grid
from wx.grid import GridCellEditor

from os import linesep
from .contentassist import ExpandingContentAssistTextCtrl
from .editordialogs import UserKeywordNameDialog, ScalarVariableDialog, ListVariableDialog
from .gridbase import GridEditor
from .gridcolorizer import Colorizer
from .tooltips import GridToolTips
from .. import robotapi
from ..context import IS_MAC
from ..controller.cellinfo import tip_message, ContentType, CellType
from ..controller.ctrlcommands import ChangeCellValue, clear_area, \
    paste_area, delete_rows, add_rows, comment_rows, insert_cells, delete_cells, \
    uncomment_rows, Undo, Redo, RenameKeywordOccurrences, ExtractKeyword, \
    add_keyword_from_cells, MoveRowsUp, MoveRowsDown, extract_scalar, extract_list, \
    insert_area, sharp_comment_rows, sharp_uncomment_rows
from ..editor.cellrenderer import CellRenderer
from ..pluginapi import Plugin
from ..publish import RideItemStepsChanged, RideSaved, PUBLISHER, RideBeforeSaving
from ..ui.progress import RenameProgressObserver
from ..usages.UsageRunner import Usages, VariableUsages
from ..utils import variablematcher
from ..widgets import RIDEDialog, PopupMenu, PopupMenuItems

_DEFAULT_FONT_SIZE = 11


def requires_focus(function):
    def _row_header_selected_on_linux(self):
        return self.FindFocus() is None

    def decorated_function(self, *args):
        if not self.has_focus():
            return
        if self.has_focus() or self.IsCellEditControlShown() or _row_header_selected_on_linux(self):
            function(self, *args)

    return decorated_function


class KeywordEditor(GridEditor, Plugin):
    _no_cell = (-1, -1)
    _popup_menu_shown = False
    dirty = property(lambda self: self.controller.dirty)

    _popup_items = [
                       'Create Keyword',
                       'Extract Keyword',
                       'Extract Variable',
                       'Rename Keyword',
                       'Find Where Used',
                       'JSON Editor\tCtrl-Shift-J',
                       '---',
                       'Go to Definition\tCtrl-B',
                       '---',
                       'Undo\tCtrl-Z',
                       'Redo\tCtrl-Y',
                       '---',
                       'Make Variable\tCtrl-1',
                       'Make List Variable\tCtrl-2',
                       'Make Dict Variable\tCtrl-5',
                       '---',
                       'Comment Cells\tCtrl-Shift-3',
                       'Uncomment Cells\tCtrl-Shift-4',
                       'Move Cursor Down\tAlt-Enter',
                       '---',
                       'Comment Rows\tCtrl-3',
                       'Uncomment Rows\tCtrl-4',
                       'Move Rows Up\tAlt-Up',
                       'Move Rows Down\tAlt-Down',
                       'Swap Row Up\tCtrl-T',
                       '---',
                   ] + GridEditor._popup_items

    def __init__(self, parent, controller, tree):
        self.settings = parent.plugin.global_settings['Grid']
        self.general_settings = parent.plugin.global_settings['General']
        self.color_background = self.general_settings['background']
        self.color_foreground = self.general_settings['foreground']
        self.color_secondary_background = self.general_settings['secondary background']
        self.color_secondary_foreground = self.general_settings['secondary foreground']
        self.color_background_help = self.general_settings['background help']
        self.color_foreground_text = self.general_settings['foreground text']
        GridEditor.__init__(self, parent, len(controller.steps) + 5, max((controller.max_columns + 1), 5),
                            parent.plugin.grid_popup_creator)
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
        self._marked_cell = (-1, -1)
        self._make_bindings()
        self._write_steps(self._controller)
        self.autosize()
        self._tree = tree
        self._has_been_clicked = False
        self._counter = 0  # Workaround for double delete actions
        self._dcells = None  # Workaround for double delete actions
        self._icells = None  # Workaround for double insert actions
        self._namespace_updated = None
        self.InheritAttributes()
        # self.Refresh()
        PUBLISHER.subscribe(self._before_saving, RideBeforeSaving)
        PUBLISHER.subscribe(self._data_changed, RideItemStepsChanged)
        # PUBLISHER.subscribe(self.OnSettingsChanged, RideSettingsChanged)
        PUBLISHER.subscribe(self._ps_on_resize_grid, RideSaved)

    def _namespace_updated(self):
        if not self._updating_namespace:
            self._updating_namespace = True
            # See following issue for history of the next line:
            # http://code.google.com/p/robotframework-ride/issues/detail?id=1108
            wx.CallAfter(
                wx.CallLater, 200, self._update_based_on_namespace_change)

    def update_value(self):
        # will be called in _RobotTableEditor._settings_changed
        pass

    def _update_based_on_namespace_change(self):
        try:
            self._colorize_grid()
        finally:
            self._updating_namespace = False

    def _ps_on_resize_grid(self, message):
        _ = message
        self._resize_grid()

    @requires_focus
    def _resize_grid(self):
        if self.settings.get("auto size cols", False):
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
            self.Bind(grid.EVT_GRID_CMD_COL_SIZE, self.on_cell_col_size_changed)
        else:
            self.Unbind(grid.EVT_GRID_CMD_COL_SIZE)

        if word_wrap:
            self.SetDefaultRowSize(wx.grid.GRID_AUTOSIZE)
        self.SetDefaultCellOverflow(False)  # DEBUG
        self.autosize()
        self._colorize_grid()

    def _configure_grid(self):
        self._set_cells()
        self.SetDefaultEditor(ContentAssistCellEditor(self._plugin, self._controller))
        self._set_fonts()

    def _set_fonts(self, update_cells=False):
        _ = update_cells
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
        self.Bind(grid.EVT_GRID_EDITOR_SHOWN, self.on_editor)
        self.Bind(wx.EVT_KEY_DOWN, self.on_key_down)
        self.Bind(wx.EVT_CHAR, self.on_char)
        self.Bind(wx.EVT_KEY_UP, self.on_key_up)
        self.GetGridWindow().Bind(wx.EVT_MOTION, self.on_motion)
        self.Bind(grid.EVT_GRID_CELL_LEFT_CLICK, self.on_cell_left_click)
        self.Bind(grid.EVT_GRID_LABEL_RIGHT_CLICK, self.on_label_right_click)
        self.Bind(grid.EVT_GRID_LABEL_LEFT_CLICK, self.on_label_left_click)
        self.Bind(wx.EVT_KILL_FOCUS, self.on_kill_focus)

    def get_tooltip_content(self):
        if self.IsCellEditControlShown() or self._popup_menu_shown:
            return ''
        cell = self.cell_under_cursor
        cell_info = self._controller.get_cell_info(cell.Row, cell.Col)
        return tip_message(cell_info)

    def on_settings_changed(self, message):
        """Redraw the colors if the color settings are modified"""
        section, setting = message.keys
        if section == 'Grid':
            if 'font' in setting:
                self._set_fonts(update_cells=True)
            elif ('col size' in setting
                  or 'max col size' in setting
                  or 'auto size cols' in setting
                  or 'word wrap' in setting):
                self._set_cells()
                return
            self.autosize()
            self._colorize_grid()

    def on_select_cell(self, event):
        self._cell_selected = True
        GridEditor.on_select_cell(self, event)
        self._colorize_grid()
        event.Skip()

    def on_kill_focus(self, event):
        self._tooltips.hide()
        self._hide_link_if_necessary()
        event.Skip()

    def _execute(self, command):
        return self._controller.execute(command)

    def _toggle_underlined(self, cell, clear=False):
        font = self.GetCellFont(cell.Row, cell.Col)
        toggle = not font.GetUnderlined() if not clear else False
        self._marked_cell = cell if toggle else (-1, -1)
        font.SetUnderlined(toggle)
        self.SetCellFont(cell.Row, cell.Col, font)
        self.Refresh()

    def on_label_right_click(self, event):
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
        popupitems = [
                    'Comment Rows\tCtrl-3',
                    'Uncomment Rows\tCtrl-4',
                    'Move Rows Up\tAlt-Up',
                    'Move Rows Down\tAlt-Down',
                    'Swap Row Up\tCtrl-T',
                    'Insert Rows\tCtrl-I',
                    'Delete Rows\tCtrl-D',
                    '---',
                    'Comment Cells\tCtrl-Shift-3',
                    'Uncomment Cells\tCtrl-Shift-4',
                    ]
        PopupMenu(self, PopupMenuItems(self, popupitems))
        event.Skip()

    def _col_label_right_click(self, event):
        # Make sonerlint happy
        pass

    def on_label_left_click(self, event):
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
        # Make sonerlint happy
        pass

    def on_move_cursor_down(self, event=None):
        self._move_cursor_down(event)

    def on_insert_rows(self, event):
        self._execute(add_rows(self.selection.rows()))
        self.ClearSelection()
        self._resize_grid()
        self._skip_except_on_mac(event)

    @staticmethod
    def _skip_except_on_mac(event):  # DEBUG Do we still need this?
        if event is not None and not IS_MAC:
            # print("DEBUG skip!")
            event.Skip()

    def on_insert_cells(self, event=None):
        # DEBUG remove below workaround for double actions
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
        self._execute(insert_cells(self.selection.topleft,
                                   self.selection.bottomright))
        self._resize_grid()
        self._skip_except_on_mac(event)

    def on_delete_cells(self, event=None):
        # DEBUG remove below workaround for double actions
        if self._counter == 1:
            if self._dcells == (self.selection.topleft,
                                self.selection.bottomright):
                self._counter = 0
                self._dcells = None
                return
        else:
            self._counter = 1

        self._dcells = (self.selection.topleft, self.selection.bottomright)
        self._execute(delete_cells(self.selection.topleft, self.selection.bottomright))
        self._resize_grid()
        self._skip_except_on_mac(event)

    # DEBUG @requires_focus
    def on_comment_rows(self, event=None):
        self._execute(comment_rows(self.selection.rows()))
        self._resize_grid()
        self._skip_except_on_mac(event)

    # DEBUG @requires_focus
    def on_uncomment_rows(self, event=None):
        self._execute(uncomment_rows(self.selection.rows()))
        self._resize_grid()
        self._skip_except_on_mac(event)

    def on_sharp_comment_rows(self, event=None):
        self._execute(sharp_comment_rows(self.selection.rows()))
        self._resize_grid()
        self._skip_except_on_mac(event)

    def on_sharp_uncomment_rows(self, event=None):
        self._execute(sharp_uncomment_rows(self.selection.rows()))
        self._resize_grid()
        self._skip_except_on_mac(event)

    def on_move_rows_up(self, event=None):
        _ = event
        self._row_move(MoveRowsUp, -1)

    def on_move_rows_down(self, event=None):
        _ = event
        self._row_move(MoveRowsDown, 1)

    def on_swap_row_up(self, event=None):
        _ = event
        self._row_move(MoveRowsUp, 1, True)

    def _row_move(self, command, change, swap=False):
        # Workaround for double actions, see issue #2048
        if self._counter == 1:
            if IS_MAC:
                row = self.GetGridCursorRow() + change
                col = self.GetGridCursorCol()
                if row >= 0:
                    self.SetGridCursor(row, col)
                self._counter = 0
                return
        else:
            self._counter += 1
        rows = self.selection.rows()
        if self._execute(command(rows)):
            if swap:
                wx.CallAfter(self._select_rows, [r for r in rows])
            else:
                wx.CallAfter(self._select_rows, [r + change for r in rows])
        self._resize_grid()

    def _select_rows(self, rows):
        self.ClearSelection()
        for r in rows:
            self.SelectRow(r, True)

    def on_motion(self, event):
        if IS_MAC and self.IsCellEditControlShown():
            return
        event.Skip()

    def _before_saving(self, message):
        _ = message
        if self.IsCellEditControlShown():
            # Fix: cannot save modifications in edit mode
            # Exit edit mode before saving
            self.HideCellEditControl()
            self.SaveEditControlValue()
            self.SetFocus()

    def _data_changed(self, message):
        if self._controller == message.item:
            self._write_steps(message.item)

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
        col = 0
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

    @staticmethod
    def _format_comments(data):
        # DEBUG: This should be moved to robot.model
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
    def on_copy(self, event=None):
        _ = event
        # print("DEBUG: OnCopy called event %s\n" % str(event))
        self.copy()

    # DEBUG @requires_focus
    def on_cut(self, event=None):
        self._clipboard_handler.cut()
        self.on_delete(event)

    def on_delete(self, event=None):
        _ = event
        if not self.IsCellEditControlShown():
            self._execute(clear_area(self.selection.topleft,
                                     self.selection.bottomright))
            self._resize_grid()

    # DEBUG    @requires_focus
    def on_paste(self, event=None):
        _ = event
        if self.IsCellEditControlShown():
            self.paste()
        else:
            self._execute_clipboard_command(paste_area)
        self._resize_grid()

    def _execute_clipboard_command(self, command_class):
        if not self.IsCellEditControlShown():
            data = self._clipboard_handler.clipboard_content()
            if data:
                data = [[data]] if isinstance(data, str) else data
                self._execute(command_class(self.selection.topleft, data))

    # DEBUG @requires_focus
    def on_insert(self, event=None):
        _ = event
        self._execute_clipboard_command(insert_area)
        self._resize_grid()

    def on_delete_rows(self, event):
        self._execute(delete_rows(self.selection.rows()))
        self.ClearSelection()
        self._resize_grid()
        self._skip_except_on_mac(event)

    # DEBUG @requires_focus
    def on_undo(self, event=None):
        _ = event
        if not self.IsCellEditControlShown():
            self._execute(Undo())
        else:
            self.GetCellEditor(*self.selection.cell).Reset()
        self._resize_grid()

    # DEBUG @requires_focus
    def on_redo(self, event=None):
        _ = event
        self._execute(Redo())
        self._resize_grid()

    def close(self):
        self._colorizer.close()
        self.save()
        PUBLISHER.unsubscribe_all(self)
        if self._namespace_updated:
            # Prevent re-entry to unregister method
            self._controller.datafile_controller.unregister_namespace_updates(
                self._namespace_updated)
        self._namespace_updated = None

    def save(self):
        self._tooltips.hide()
        if self.IsCellEditControlShown():
            cell_editor = self.GetCellEditor(*self.selection.cell)
            cell_editor.EndEdit(self.selection.topleft.row,
                                self.selection.topleft.col, self)

    def show_content_assist(self):
        if self.IsCellEditControlShown():
            self.GetCellEditor(*self.selection.cell).show_content_assist(self.selection.cell)

    def refresh_datafile(self, item, event):
        self._tree.refresh_datafile(item, event)

    @staticmethod
    def _calculate_position():
        x, y = wx.GetMousePosition()
        return x, y + 20

    def on_editor(self, event):
        self._tooltips.hide()
        row_height = self.GetRowSize(self.selection.topleft.row)
        self.GetCellEditor(*self.selection.cell).SetHeight(row_height)
        event.Skip()

    def _move_cursor_down(self, event):
        self.DisableCellEditControl()
        if event:
            try:
                shiftdown = event.ShiftDown()
            except AttributeError:
                shiftdown = False
        else:
            shiftdown = False
        self.MoveCursorDown(shiftdown)

    def _call_ctrl_shift_function(self, event: object, keycode: int):
        if keycode == ord('I'):
            self.on_insert_cells()
        elif keycode == ord('J'):
            self.on_json_editor(event)
        elif keycode == ord('D'):
            self.on_delete_cells()
        """
        elif keycode == ord('3'):
            self._open_cell_editor_and_execute_sharp_comment()
        elif keycode == ord('4'):
            self._open_cell_editor_and_execute_sharp_uncomment()
        """
        return True

    def _call_ctrl_function(self, event: object, keycode: int):
        if keycode == wx.WXK_SPACE:
            self._open_cell_editor_with_content_assist()
            return False  # event must not be skipped in this case
        elif keycode == ord('C'):
            self.on_copy(event)
        elif keycode == ord('X'):
            self.on_cut(event)
        elif keycode == ord('V'):
            self.on_paste(event)
        elif keycode == ord('Z'):
            self.on_undo(event)
        elif keycode == ord('A'):
            self.on_select_all(event)
        elif keycode == ord('B'):
            self._navigate_to_matching_user_keyword(
                self.GetGridCursorRow(), self.GetGridCursorCol())
        elif keycode == ord('F'):
            if not self.has_focus():
                self.SetFocus()  # Avoiding Search field on Text Edit
        elif keycode in (ord('1'), ord('2'), ord('5')):
            self._open_cell_editor_and_execute_variable_creator(
                list_variable=(keycode == ord('2')),
                dict_variable=(keycode == ord('5')))
        elif keycode == ord('T'):
            self._row_move(MoveRowsUp, 1, True)
        else:
            self.show_cell_information()
        return True

    def _call_direct_function(self, event: object, keycode: int):
        if keycode == wx.WXK_WINDOWS_MENU:
            self.on_cell_right_click(event)
        elif keycode == wx.WXK_BACK:
            self._move_grid_cursor(event, keycode)
        elif keycode == wx.WXK_RETURN:
            if self.IsCellEditControlShown():
                # fill auto-suggestion into cell when pressing enter
                self._get_cell_editor().update_from_suggestion_list()
                self._move_grid_cursor(event, keycode)
            else:
                self.open_cell_editor()
            return False  # event must not be skipped in this case
        elif keycode == wx.WXK_F2:
            self.open_cell_editor()
        return True

    def _call_alt_function(self, event, keycode: int):
        if keycode == wx.WXK_SPACE:
            self._open_cell_editor_with_content_assist()  # Mac CMD
        elif keycode == wx.WXK_RETURN:
            if self.IsCellEditControlShown():
                event.GetEventObject().WriteText(linesep)
            else:
                self._move_cursor_down(event)
            return False  # event must not be skipped in this case
        return True

        """
        elif keycode in [wx.WXK_DOWN, wx.WXK_UP]:
            print(f"DEBUG kweditor call move_rews ky={keycode}")
            # Mac Option key(⌥)
            self._move_rows(keycode)
        """

    def on_key_down(self, event):
        keycode = event.GetUnicodeKey() or event.GetKeyCode()
        if event.ControlDown():
            if event.ShiftDown():
                skip = self._call_ctrl_shift_function(event, keycode)
            else:
                skip = self._call_ctrl_function(event, keycode)
        elif event.AltDown():
            skip = self._call_alt_function(event, keycode)
        else:
            skip = self._call_direct_function(event, keycode)
        if skip:
            event.Skip()

    def on_char(self, event):
        key_char = event.GetUnicodeKey()
        if key_char < ord(' '):
            return
        if key_char in [ord('['), ord('{'), ord('('), ord("'"), ord('\"'), ord('`')]:
            self.open_cell_editor().execute_enclose_text(chr(key_char))
        else:
            event.Skip()

    def on_go_to_definition(self, event):
        _ = event
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
            self.on_move_rows_up()
        else:
            self.on_move_rows_down()

    def _move_grid_cursor(self, event, keycode):
        self.DisableCellEditControl()
        if keycode == wx.WXK_RETURN:
            self.MoveCursorRight(event.ShiftDown())
        else:
            self.MoveCursorLeft(event.ShiftDown())

    def move_grid_cursor_and_edit(self):
        # self.MoveCursorRight(False)
        self.open_cell_editor()

    def on_key_up(self, event):
        event.Skip()  # DEBUG seen this skip as soon as possible
        self._tooltips.hide()
        self._hide_link_if_necessary()
        #  event.Skip()

    def _get_cell_editor(self):
        row = self.GetGridCursorRow()
        return self.GetCellEditor(self.GetGridCursorCol(), row)

    def open_cell_editor(self):
        if not self.IsCellEditControlEnabled():
            self.EnableCellEditControl()
        cell_editor = self._get_cell_editor()
        cell_editor.Show(True)
        return cell_editor

    def _open_cell_editor_with_content_assist(self):
        # print(f"DEBUG: kweditor call _open_cell_editor_with_content_assist")
        wx.CallAfter(self.open_cell_editor().show_content_assist)
        # wx.CallAfter(self._move_grid_cursor, wx.grid.GridEvent(), wx.WXK_RETURN)

    def _open_cell_editor_and_execute_variable_creator(self, list_variable=False,
                                                       dict_variable=False):
        cell_editor = self.open_cell_editor()
        wx.CallAfter(cell_editor.execute_variable_creator,
                     list_variable, dict_variable)

    def on_make_variable(self, event):
        _ = event
        self._open_cell_editor_and_execute_variable_creator(list_variable=False)

    def on_make_list_variable(self, event):
        _ = event
        self._open_cell_editor_and_execute_variable_creator(list_variable=True)

    def on_make_dict_variable(self, event):
        _ = event
        self._open_cell_editor_and_execute_variable_creator(dict_variable=True)

    def _open_cell_editor_and_execute_sharp_comment(self):
        # Meant for a single cell selection!
        wx.CallAfter(self.open_cell_editor().execute_sharp_comment)

    def _open_cell_editor_and_execute_sharp_uncomment(self):
        # Meant for a single cell selection!
        wx.CallAfter(self.open_cell_editor().execute_sharp_uncomment)

    def current_cell(self):
        curcell = [self.GetGridCursorRow(), self.GetGridCursorCol()]
        return curcell

    def on_comment_cells(self, event):
        _ = event
        if self.GetSelectionBlockTopLeft():
            self.on_sharp_comment_rows(event)
        else:
            self._open_cell_editor_and_execute_sharp_comment()

    def on_uncomment_cells(self, event):
        _ = event
        if self.GetSelectionBlockTopLeft():
            self.on_sharp_uncomment_rows(event)
        else:
            self._open_cell_editor_and_execute_sharp_uncomment()

    def on_cell_right_click(self, event):
        self._tooltips.hide()
        self._popup_menu_shown = True
        GridEditor.on_cell_right_click(self, event)
        self._popup_menu_shown = False

    def on_select_all(self, event):
        _ = event
        self.SelectAll()

    def on_cell_col_size_changed(self, event):
        wx.CallAfter(self.AutoSizeRows, False)
        event.Skip()

    def on_cell_left_click(self, event):
        self._tooltips.hide()
        if event.ControlDown():
            if self._navigate_to_matching_user_keyword(event.Row, event.Col):
                return
        if not self._has_been_clicked:
            self.SetGridCursor(event.Row, event.Col)
            self._has_been_clicked = True
        else:
            event.Skip()

    def _navigate_to_matching_user_keyword(self, row, col):
        value = self.GetCellValue(row, col)
        uk = self._plugin.get_user_keyword(value)
        if uk:
            self._toggle_underlined((grid.GridCellCoords(row, col)), True)
            wx.CallAfter(self._tree.select_user_keyword_node, uk)
            return True
        return False

    def _is_active_window(self):
        return self.IsShownOnScreen() and self.FindFocus()

    def _hide_link_if_necessary(self):
        if self._marked_cell == (-1, -1):
            return
        self._toggle_underlined(self._marked_cell, True)

    def on_create_keyword(self, event):
        _ = event
        cells = self._data_cells_from_current_row()
        if not cells:
            return
        try:
            self._execute(add_keyword_from_cells(cells))
        except ValueError as err:
            wx.MessageBox(str(err))

    def _data_cells_from_current_row(self):
        currow, curcol = self.selection.cell
        rowdata = self._row_data(currow)[curcol:]
        return self._strip_trailing_empty_cells(self._remove_comments(rowdata))

    @staticmethod
    def _remove_comments(data):
        for index, cell in enumerate(data):
            if cell.strip().startswith('#'):
                return data[:index]
        return data

    def on_extract_keyword(self, event):
        _ = event
        dlg = UserKeywordNameDialog(self._controller)
        if dlg.ShowModal() == wx.ID_OK:
            name, args = dlg.get_value()
            rows = self.selection.topleft.row, self.selection.bottomright.row
            self._execute(ExtractKeyword(name, args, rows))

    def on_extract_variable(self, event):
        _ = event
        cells = self.selection.cells()
        if len(cells) == 1:
            self._extract_scalar(cells[0])
        elif min(row for row, _ in cells) == max(row for row, _ in cells):
            self._extract_list(cells)
        self._resize_grid()

    def on_find_where_used(self, event):
        _ = event
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

    @staticmethod
    def _cell_value_contains_multiple_search_items(value):
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
            self._execute(extract_scalar(name, value, comment, cell))

    def _extract_list(self, cells):
        var = robotapi.Variable(
            self._controller.datafile.variable_table,
            '', [self.GetCellValue(*cell) for cell in cells], '')
        dlg = ListVariableDialog(
            self._controller.datafile_controller.variables, var, self._plugin)
        if dlg.ShowModal() == wx.ID_OK:
            name, value = dlg.get_value()
            comment = dlg.get_comment()
            self._execute(extract_list(name, value, comment, cells))

    def on_rename_keyword(self, event):
        _ = event
        old_name = self._current_cell_value()
        if not old_name.strip() or variablematcher.is_variable(old_name):
            return
        new_name = wx.GetTextFromUser('New name', 'Rename Keyword',
                                      default_value=old_name)
        if new_name:
            self._execute(RenameKeywordOccurrences(
                old_name, new_name, RenameProgressObserver(self.GetParent())))

    # Add one new Dialog to edit pretty json String TODO: use better editor with more functions
    def on_json_editor(self, event=None):
        if event:
            event.Skip()
        dialog = RIDEDialog()
        dialog.SetTitle('JSON Editor')
        dialog.SetSizer(wx.BoxSizer(wx.HORIZONTAL))
        ok_btn = wx.Button(dialog, wx.ID_OK, "Save")
        cnl_btn = wx.Button(dialog, wx.ID_CANCEL, "Cancel")
        rich_text = wx.TextCtrl(dialog, wx.ID_ANY, "If supported by the native control, this is reversed, and this is"
                                                   " a different font.", size=(400, 475),
                                style=wx.HSCROLL | wx.TE_MULTILINE | wx.TE_NOHIDESEL)
        dialog.Sizer.Add(rich_text, flag=wx.GROW, proportion=1)
        dialog.Sizer.Add(ok_btn, flag=wx.ALL)
        dialog.Sizer.Add(cnl_btn, flag=wx.ALL)
        # Get cell value of parent grid
        if self.is_json(self._current_cell_value()):
            json_str = json.loads(self._current_cell_value())
            rich_text.SetValue(json.dumps(json_str, indent=4, ensure_ascii=False))
        else:
            rich_text.SetValue(self._current_cell_value())
        dialog.SetSize((650, 550))
        # If click Save, then save the value in richText into the original
        # grid cell, and clear all indent.
        if dialog.ShowModal() == wx.ID_OK:
            content = rich_text.GetValue()
            if self.is_json(content):
                str_json = json.loads(content)
                self.cell_value_edited(self.selection.cell[0], self.selection.cell[1],
                                       json.dumps(str_json, ensure_ascii=False))
            else:
                try:
                    json.loads(content)  # Yes, we need the error
                except JSONDecodeError as e:
                    res = wx.MessageDialog(dialog, f"Error in JSON: {e}\n\nSave anyway?",
                                           "Validation Error!", wx.YES_NO)
                    res.InheritAttributes()
                    response = res.ShowModal()
                    if response == wx.ID_YES:
                        self.cell_value_edited(self.selection.cell[0],
                                               self.selection.cell[1],
                                               rich_text.GetValue())

    # If the json_str is json format, then return True
    @staticmethod
    def is_json(json_str):
        try:
            json.loads(json_str)
        except JSONDecodeError:
            return False
        return True


class ContentAssistCellEditor(GridCellEditor):

    def __init__(self, plugin, controller):
        self.settings = plugin.global_settings['Grid']
        self.general_settings = plugin.global_settings['General']
        self.filter_newlines = self.settings.get("filter newlines", True)
        self.color_background_help = self.general_settings['background help']
        self.color_foreground_text = self.general_settings['foreground text']
        GridCellEditor.__init__(self)
        self._plugin = plugin
        self._controller = controller
        self._grid = None
        self._original_value = None
        self._value = None
        self._tc = None
        self._counter = 0
        self._height = 0

    def show_content_assist(self, args=None):
        _ = args
        if self._tc:
            self._tc.show_content_assist()

    def update_from_suggestion_list(self):
        if self._tc and self._tc.is_shown():
            self._tc.fill_suggestion()

    def execute_variable_creator(self, list_variable=False,
                                 dict_variable=False):
        self._tc.execute_variable_creator(list_variable, dict_variable)

    def execute_enclose_text(self, keycode):
        self._tc.execute_enclose_text(keycode)

    def execute_sharp_comment(self):
        self._tc.execute_sharp_comment()

    def execute_sharp_uncomment(self):
        self._tc.execute_sharp_uncomment()

    def Create(self, parent, idd, evthandler):
        self._tc = ExpandingContentAssistTextCtrl(parent, self._plugin, self._controller)
        self.SetControl(self._tc)
        if evthandler:
            self._tc.PushEventHandler(evthandler)

    def SetSize(self, rect):
        self._tc.SetSize(rect.x, rect.y, rect.width + 2, rect.height + 2, wx.SIZE_ALLOW_MINUS_ONE)

    def SetHeight(self, height):
        self._height = height

    def BeginEdit(self, row, col, gridd):
        self._counter = 0
        self._tc.SetSize((-1, self._height))
        self._tc.SetBackgroundColour(self.color_background_help)  # DEBUG: We are now in Edit mode
        self._tc.SetForegroundColour(self.color_foreground_text)
        self._tc.set_row(row)
        self._original_value = gridd.GetCellValue(row, col)
        if self._original_value:
            if self.filter_newlines:
                temp_value = self._original_value.replace(r'\n', '\\n')
                self._tc.SetValue(temp_value)
            else:
                self._tc.SetValue(self._original_value)
        self._tc.SetSelection(0, self._tc.GetLastPosition())
        self._tc.SetFocus()
        self._grid = gridd

    def EndEdit(self, row, col, gridd, *ignored):
        value = self._get_value()
        if value and self.filter_newlines:
            temp_value = value.replace('\\n', r'\n')
            value = temp_value
        if value != self._original_value:
            self._value = value
            wx.CallAfter(self._grid.move_grid_cursor_and_edit)
            return value
        else:
            self._tc.hide()
            gridd.SetFocus()

    def ApplyEdit(self, row, col, gridd):
        val = self._tc.GetValue()
        gridd.GetTable().SetValue(row, col, val)  # update the table
        self._original_value = ''
        self._tc.SetValue('')
        # if self._value and val != '':  # DEBUG Fix #1967 crash when click other cell
        # this will cause deleting all text in edit mode not working
        self._grid.cell_value_edited(row, col, self._value)

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
            # print(f"DEBUG: Delete key at ContentAssist key {key}")
            self._grid.HideCellEditControl()
        elif key == wx.WXK_BACK:
            self._tc.SetValue(self._original_value)
        else:
            self._tc.SetValue(chr(key))
        self._tc.SetFocus()
        self._tc.SetInsertionPointEnd()

    def Clone(self):
        return ContentAssistCellEditor(self._plugin, self._controller)


class ChooseUsageSearchStringDialog(wx.Dialog):

    def __init__(self, cellvalue):
        wx.Dialog.__init__(self, None, wx.ID_ANY, "Find Where Used",
                           style=wx.DEFAULT_DIALOG_STYLE)
        """
        self.SetBackgroundColour(Colour(200, 222, 40))
        self.SetForegroundColour(Colour(7, 0, 70))
        """
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
