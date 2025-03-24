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

import builtins
import json
from json.decoder import JSONDecodeError
from multiprocessing import shared_memory

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
from ..publish import RideItemStepsChanged, RideSaved, PUBLISHER, RideBeforeSaving, RideSettingsChanged
from ..ui.progress import RenameProgressObserver
from ..usages.UsageRunner import Usages, VariableUsages
from ..utils import variablematcher
from ..widgets import RIDEDialog, PopupMenu, PopupMenuItems

_ = wx.GetTranslation  # To keep linter/code analyser happy
builtins.__dict__['_'] = wx.GetTranslation

_DEFAULT_FONT_SIZE = 11
COL_HEADER_EDITOR = wx.NewId()
PLUGIN_NAME = 'Editor'
ZOOM_FACTOR = 'zoom factor'
INS_ROWS = 'Insert Rows\tCtrl-I'
DEL_ROWS = 'Delete Rows\tCtrl-D'
CMT_CELLS = 'Comment Cells\tCtrl-Shift-3'
UCMT_CELLS = 'Uncomment Cells\tCtrl-Shift-4'
MV_CUR_DWN = 'Move Cursor Down\tAlt-Enter'
CMT_ROWS = 'Comment Rows\tCtrl-3'
UCMT_ROWS = 'Uncomment Rows\tCtrl-4'
MV_ROWS_UP = 'Move Rows Up\tAlt-Up'
MV_ROWS_DWN = 'Move Rows Down\tAlt-Down'
SWAP_ROWS_UP = 'Swap Row Up\tCtrl-T'
REN_KW = 'Rename Keyword'

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

    def __init__(self, parent, controller, tree):
        self.settings = parent.plugin.global_settings['Grid']
        self.zoom = self.settings.get(ZOOM_FACTOR, 0)
        self.general_settings = parent.plugin.global_settings['General']
        self.color_background = self.general_settings['background']
        self.color_foreground = self.general_settings['foreground']
        self.color_secondary_background = self.general_settings['secondary background']
        self.color_secondary_foreground = self.general_settings['secondary foreground']
        self.color_background_help = self.general_settings['background help']
        self.color_foreground_text = self.general_settings['foreground text']
        GridEditor.__init__(self, parent, len(controller.steps) + 5, max((controller.max_columns + 1), 5),
                            parent.plugin.grid_popup_creator)
        self._popup_items = ([
                             _('Insert Cells\tCtrl-Shift-I'), _('Delete Cells\tCtrl-Shift-D'),
                             _(INS_ROWS), _(DEL_ROWS), '---',
                             _('Select All\tCtrl-A'), '---', _('Cut\tCtrl-X'), _('Copy\tCtrl-C'),
                             _('Paste\tCtrl-V'), _('Insert\tCtrl-Shift-V'), '---', _('Delete\tDel'),
                             '---'] +
                             [
                              _('Create Keyword'),
                              _('Extract Keyword'),
                              _('Extract Variable'),
                              _(REN_KW),
                              _('Find Where Used'),
                              _('JSON Editor\tCtrl-Shift-J'),
                              '---',
                              _('Go to Definition\tCtrl-B'),
                              '---',
                              _('Undo\tCtrl-Z'),
                              _('Redo\tCtrl-Y'),
                              '---',
                              _('Make Variable\tCtrl-1'),
                              _('Make List Variable\tCtrl-2'),
                              _('Make Dict Variable\tCtrl-5'),
                              '---',
                              _(CMT_CELLS),
                              _(UCMT_CELLS),
                              _(MV_CUR_DWN),
                              '---',
                              _(CMT_ROWS),
                              _(UCMT_ROWS),
                              _(MV_ROWS_UP),
                              _(MV_ROWS_DWN),
                              _(SWAP_ROWS_UP)
                              ])
        self._popup_items_nt = ([
                                 'Insert Cells\tCtrl-Shift-I', 'Delete Cells\tCtrl-Shift-D',
                                 INS_ROWS, DEL_ROWS, '---',
                                 'Select All\tCtrl-A', '---', 'Cut\tCtrl-X', 'Copy\tCtrl-C',
                                 'Paste\tCtrl-V', 'Insert\tCtrl-Shift-V', '---', 'Delete\tDel',
                                 '---'] +
                                [
                                'Create Keyword',
                                'Extract Keyword',
                                'Extract Variable',
                                REN_KW,
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
                                CMT_CELLS,
                                UCMT_CELLS,
                                MV_CUR_DWN,
                                '---',
                                CMT_ROWS,
                                UCMT_ROWS,
                                MV_ROWS_UP,
                                MV_ROWS_DWN,
                                SWAP_ROWS_UP
                                ])
        self._parent = parent
        self._plugin = parent.plugin
        self._cell_selected = False
        self._colorizer = Colorizer(self, controller)
        self._controller = controller
        try:
            set_lang = shared_memory.ShareableList(name="language")
            self._language = [set_lang[0]]
            # print(f"DEBUG: settings.py SettingEditor __init__ SHAREDMEM language={self._language}")
        except AttributeError:
            try:
                self._language = self._controller.language
                # print(f"DEBUG: settings.py SettingEditor __init__ CONTROLLER language={self._language}")
            except AttributeError:
                self._language = ['en']
        self._language = self._language[0] if isinstance(self._language, list) else self._language
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
        self._spacing = self._plugin.global_settings['txt number of spaces']
        self._namespace_updated = None
        self.InheritAttributes()
        self.col_label_element = None
        # self.Refresh()
        PUBLISHER.subscribe(self._before_saving, RideBeforeSaving)
        PUBLISHER.subscribe(self._data_changed, RideItemStepsChanged)
        PUBLISHER.subscribe(self.on_settings_changed, RideSettingsChanged)
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
        self.SetFocus()

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
        self.SetDefaultEditor(ContentAssistCellEditor(self._plugin, self._controller, self._language))
        self._set_fonts()
        wx.CallAfter(self.SetGridCursor, (0, 0))  # To make cells colorized as soon we select keywords or tests
        wx.CallAfter(self.highlight, '')
        # wx.CallAfter(self.GoToCell,  (0, 0))  # To make cells colorized as soon we select keywords or tests

    def _set_fonts(self, update_cells=False):
        _ = update_cells
        font_size = self.settings.get('font size', _DEFAULT_FONT_SIZE) + self.zoom
        font_family = wx.FONTFAMILY_MODERN if self.settings['fixed font'] \
            else wx.FONTFAMILY_DEFAULT
        font_face = self.settings.get('font face', None)
        if font_face is None:
            font = wx.Font(font_size, font_family, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
            self.settings.set('font face', font.GetFaceName())
        else:
            font = wx.Font(font_size, font_family, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, font_face)
        self.SetDefaultCellFont(font)
        self.SetLabelFont(font)
        col_size = max(0, font_size)+self.zoom
        row_size = max(20, font_size)+self.zoom
        self.SetRowLabelSize(row_size)
        self.SetColLabelSize(col_size)
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
        self.Bind(grid.EVT_GRID_LABEL_LEFT_DCLICK, self._col_label_right_click)
        self.Bind(grid.EVT_GRID_LABEL_LEFT_CLICK, self.on_label_left_click)
        self.Bind(wx.EVT_KILL_FOCUS, self.on_kill_focus)
        self.Bind(wx.EVT_MOUSEWHEEL, self.on_zoom)

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
            if ZOOM_FACTOR in setting:
                self.zoom = self.settings.get(ZOOM_FACTOR, 0)
            if 'font' in setting or ZOOM_FACTOR in setting:
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
        rows = self._is_whole_row_selection()
        if rows:
            self.ClearSelection()
            self.GoToCell(rows[0], 0)
            wx.CallAfter(self.SelectBlock, rows[0], 0, rows[-1], self.NumberCols-1)
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
            if event.Row != -1:
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
                    _(INS_ROWS),
                    _(DEL_ROWS),
                    _(CMT_ROWS),
                    _(UCMT_ROWS),
                    _(MV_ROWS_UP),
                    _(MV_ROWS_DWN),
                    _(SWAP_ROWS_UP),
                    '---',
                    _(CMT_CELLS),
                    _(UCMT_CELLS),
                    ]
        popupitems_nt = [
                    INS_ROWS,
                    DEL_ROWS,
                    CMT_ROWS,
                    UCMT_ROWS,
                    MV_ROWS_UP,
                    MV_ROWS_DWN,
                    SWAP_ROWS_UP,
                    '---',
                    CMT_CELLS,
                    UCMT_CELLS,
                    ]
        PopupMenu(self, PopupMenuItems(self, popupitems, popupitems_nt))
        event.Skip()

    def _col_label_right_click(self, event):
        if event.Col < 0:
            return
        headers = self._controller.data.parent.header[1:]
        if (not headers and event.Col == 0) or (headers and event.Col == len(headers)):
            self._controller.data.parent.header.append('')
        if event.Col + 1 < len(self._controller.data.parent.header) + 1:
            value = self._controller.data.parent.header[event.Col+1]
            lpos = self.GetColLeft(event.Col)
            whandle = self.GetGridColLabelWindow()
            font_size = self.GetLabelFont().GetPixelSize().width + 4
            col_size = max(max(4, len(value))*font_size, self.GetColSize(event.Col))
            edit = wx.TextCtrl(whandle, COL_HEADER_EDITOR, value, size=(col_size, -1),
                               style=wx.TE_PROCESS_ENTER | wx.TE_NOHIDESEL)
            epos = edit.GetPosition()
            edit.SetPosition((lpos, epos[1]))
            edit.Bind(wx.EVT_KEY_DOWN, self.on_col_label_edit)
            edit.Bind(wx.EVT_KEY_UP, self.on_col_label_edit)
            edit.SetInsertionPointEnd()
            edit.SelectAll()
            edit.SetFocus()
            self.col_label_element = (edit, event.Col)
            self._marked_cell = (-1, -1)
            # edit.Bind(wx.EVT_KILL_FOCUS, self.on_kill_focus)

    def on_col_label_edit(self, event: wx.KeyEvent):
        keycode = event.GetKeyCode()
        edit, col = self.col_label_element
        if keycode == wx.WXK_ESCAPE:
            wx.CallAfter(edit.Destroy)
        if keycode == wx.WXK_RETURN:
            value = edit.GetValue()
            if value == '':
                del self._controller.data.parent.header[col+1]
            else:
                self._controller.data.parent.header[col+1] = value
            self.SetColLabelValue(col, value)
            self.AutoSizeColumn(col)
            self._controller.mark_dirty()
            self._controller.notify_steps_changed()
            wx.CallAfter(edit.Destroy)
            return
        event.Skip()

    def on_label_left_click(self, event):
        if event.Col == -1:
            if event.Row != -1:
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
        if event.ShiftDown() or event.ControlDown():
            self.ClearSelection()
            cursor_col = self.GetGridCursorCol()
            event_col = event.Col
            start, end = (cursor_col, event_col) if cursor_col < event_col else (event_col, cursor_col)
            for col in range(start, end + 1):
                self.SelectCol(col, addToSelected=True)
        else:
            self.SelectCol(event.Col, addToSelected=False)
            self.SetGridCursor(0, event.Col)

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
        __ = event
        self._row_move(MoveRowsUp, -1)

    def on_move_rows_down(self, event=None):
        __ = event
        self._row_move(MoveRowsDown, 1)

    def on_swap_row_up(self, event=None):
        __ = event
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
            self.SetColLabelSize(20)  # DEBUG We set a small size to activate right and left clicks
            for empty_col in range(0, 26):  # DEBUG to be sure all are empty, was: self.NumberCols + 1
                self.SetColLabelValue(empty_col, '')
            return
        self.SetColLabelSize(wx.grid.GRID_AUTOSIZE)  # DEBUG
        col = 0
        for col, header in enumerate(headers):
            self.SetColLabelValue(col, header)
        for empty_col in range(col + 1, 26):  # DEBUG to be sure all are empty, was: self.NumberCols + 1
            self.SetColLabelValue(empty_col, '')

    def _colorize_grid(self):
        selection_content = self._get_single_selection_content_or_none_on_first_call()
        if selection_content is None:
            self.highlight(None)
        elif self._parent:
            # print(f"DEBUG: kweditor.py _colorize_grid parent={self._parent} name={self._parent.name}")
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
        __ = event
        # print("DEBUG: OnCopy called event %s\n" % str(event))
        self.copy()

    # DEBUG @requires_focus
    def on_cut(self, event=None):
        self.cut()
        self.on_delete(event)

    def on_delete(self, event=None):
        __ = event
        if not self.IsCellEditControlShown():
            self._execute(clear_area(self.selection.topleft,
                                     self.selection.bottomright))
            self._resize_grid()

    # DEBUG    @requires_focus
    def on_paste(self, event=None):
        __ = event
        if self.IsCellEditControlShown():
            self.paste()
        else:
            self._execute_clipboard_command(paste_area)
        self._resize_grid()

    def _execute_clipboard_command(self, command_class):
        if not self.IsCellEditControlShown():
            data = self._clipboard_handler.clipboard_content()
            if data:
                if isinstance(data, str):
                    data = [[self._string_to_cell(data)]]
                elif isinstance(data, list) and isinstance(data[0], list):
                    data = self._get_main_data(data)
                self._execute(command_class(self.selection.topleft, data))

    def _get_main_data(self, data: []) -> []:
        main_data = []
        for ldata in data:
            new_data = []
            for rdata in ldata:
                sdata = self._string_to_cell(rdata)
                new_data.append(sdata)
            main_data.append(new_data)
        return main_data

    def _string_to_cell(self, content: str) -> str:
        spaces = ' ' * self._spacing
        cells = content.replace(' | ', spaces).replace(spaces, '\t').strip()  # DEBUG: Make this cells
        return cells

    # DEBUG
    @requires_focus
    def on_insert(self, event=None):
        __ = event
        self._execute_clipboard_command(insert_area)
        self._resize_grid()

    def on_delete_rows(self, event):
        self._execute(delete_rows(self.selection.rows()))
        self.ClearSelection()
        self._resize_grid()
        self._skip_except_on_mac(event)

    # DEBUG @requires_focus
    def on_undo(self, event=None):
        __ = event
        if not self.IsCellEditControlShown():
            self._execute(Undo())
        else:
            self.GetCellEditor(*self.selection.cell).Reset()
        self._resize_grid()

    # DEBUG @requires_focus
    def on_redo(self, event=None):
        __ = event
        self._execute(Redo())
        self._resize_grid()

    def close(self):
        self._colorizer.close()
        self.save()
        PUBLISHER.unsubscribe_all(self)
        if self._namespace_updated:
            # Prevent re-entry to unregister method
            self._controller.datafile_controller.unregister_namespace_updates(self._namespace_updated)
        self._namespace_updated = None

    def save(self):
        self._tooltips.hide()
        if self.IsCellEditControlShown():
            cell_editor = self.GetCellEditor(*self.selection.cell)
            cell_editor.EndEdit(self.selection.topleft.row, self.selection.topleft.col, self)

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
            return False
        elif keycode == ord('V'):
            self.on_paste(event)
        elif keycode == ord('Z'):
            # print("DEBUG: kweditor.py _call_ctrl_function Pressed CTRL-Z")
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

    def _call_direct_function(self, event: wx.KeyEvent, keycode: int):
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

    def on_zoom(self, event):
        rotation = event.GetWheelRotation()
        ctrl_down = event.ControlDown()
        if not ctrl_down:
            event.Skip()
            return
        self._set_zoom(rotation)
        self.zoom = self.settings.get(ZOOM_FACTOR, 0)

    def _set_zoom(self, rotation):
        if rotation == 0:  # Special value to reset
            self.settings.set(ZOOM_FACTOR, 0)
            return
        new = 1 if rotation > 0 else -1  # Rotate away from user, increase, to user, decrease
        old = self.settings.get(ZOOM_FACTOR, 0)  # DEBUG: Condition to zoom limits, [-10, 10]?
        self.settings.set(ZOOM_FACTOR, old+new)

    def on_go_to_definition(self, event):
        __ = event
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
            if info.cell_type == CellType.KEYWORD and info.content_type == ContentType.STRING:
                details = _("""<b>Keyword was not detected by RIDE</b>
        <br>Possible corrections:<br>
        <ul>
            <li>Import library or resource file containing the keyword.</li>
            <li>For library import errors: Consider importing library spec XML
            (Tools / Import Library Spec XML or by adding the XML file with the
            correct name to PYTHONPATH) to enable keyword completion
            for example for Java libraries.
            Library spec XML can be created using libdoc tool from Robot Framework.</li>
        </ul>""")
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
        self.SetFocus()

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

    def _open_cell_editor_and_execute_variable_creator(self, list_variable=False, dict_variable=False):
        cell_editor = self.open_cell_editor()
        wx.CallAfter(cell_editor.execute_variable_creator, list_variable, dict_variable)

    def on_make_variable(self, event):
        __ = event
        self._open_cell_editor_and_execute_variable_creator(list_variable=False)

    def on_make_list_variable(self, event):
        __ = event
        self._open_cell_editor_and_execute_variable_creator(list_variable=True)

    def on_make_dict_variable(self, event):
        __ = event
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
        __ = event
        if self.GetSelectionBlockTopLeft():
            self.on_sharp_comment_rows(event)
        else:
            self._open_cell_editor_and_execute_sharp_comment()

    def on_uncomment_cells(self, event):
        __ = event
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
        __ = event
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
        __ = event
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
        __ = event
        dlg = UserKeywordNameDialog(self._controller)
        if dlg.ShowModal() == wx.ID_OK:
            name, args = dlg.get_value()
            rows = self.selection.topleft.row, self.selection.bottomright.row
            self._execute(ExtractKeyword(name, args, rows))

    def on_extract_variable(self, event):
        __ = event
        cells = self.selection.cells()
        if len(cells) == 1:
            self._extract_scalar(cells[0])
        elif min(row for row, _ in cells) == max(row for row, _ in cells):
            self._extract_list(cells)
        self._resize_grid()

    def on_find_where_used(self, event):
        __ = event
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
        __ = event
        old_name = self._current_cell_value()
        if not old_name.strip() or variablematcher.is_variable(old_name):
            return
        new_name = wx.GetTextFromUser(_('New name'), _(REN_KW), default_value=old_name)
        if new_name:
            self._execute(RenameKeywordOccurrences(
                old_name, new_name, RenameProgressObserver(self.GetParent()), language=self._language))

    # Add one new Dialog to edit pretty json String TODO: use better editor with more functions
    def on_json_editor(self, event=None):
        if event:
            event.Skip()
        dialog = RIDEDialog()
        dialog.SetTitle('JSON Editor')
        dialog.SetSizer(wx.BoxSizer(wx.HORIZONTAL))
        ok_btn = wx.Button(dialog, wx.ID_OK, _("Save"))
        cnl_btn = wx.Button(dialog, wx.ID_CANCEL, _("Cancel"))
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
                    res = wx.MessageDialog(dialog, f"{_('Error in JSON:')} {e}\n\n{_('Save anyway?')}",
                                           _("Validation Error!"), wx.YES_NO)
                    res.InheritAttributes()
                    response = res.ShowModal()
                    if response == wx.ID_YES:
                        self.cell_value_edited(self.selection.cell[0], self.selection.cell[1], rich_text.GetValue())

    # If the json_str is json format, then return True
    @staticmethod
    def is_json(json_str):
        try:
            json.loads(json_str)
        except JSONDecodeError:
            return False
        return True

    """
    def words_cache(self, doc_size: int):
        if doc_size != self.doc_size:
            words_list = self.collect_words(SOME_CONTENT)
            self._words_cache.update(words_list)
            self.doc_size = doc_size
        return sorted(self._words_cache)

    @staticmethod
    def collect_words(text: str):
        if not text:
            return ['']

        def var_strip(txt:str):
            return txt.strip('$&@%{[(')

        words = set()
        words_ = list(text.replace('\r\n', ' ').replace('\n', ' ').split(' '))
        for w in words_:
            wl = var_strip(w)
            if wl and wl[0].isalpha():
                words.add(w)

        print(f"DEBUG: texteditor.py SourceEditor collect_words returning {words=}")
        return sorted(words)
    """

class ContentAssistCellEditor(GridCellEditor):

    def __init__(self, plugin, controller, language='En'):
        self.settings = plugin.global_settings['Grid']
        self.general_settings = plugin.global_settings['General']
        self.filter_newlines = self.settings.get("filter newlines", True)
        self.color_background_help = self.general_settings['background help']
        self.color_foreground_text = self.general_settings['foreground text']
        GridCellEditor.__init__(self)
        self._plugin = plugin
        self._controller = controller
        self._language = language
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
        self._tc = ExpandingContentAssistTextCtrl(parent, self._plugin, self._controller, self._language)
        # self._tc.suggestion_source.update_from_local(self._controller.datafile, self._language)
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
        return ContentAssistCellEditor(self._plugin, self._controller, self._language)


class ChooseUsageSearchStringDialog(wx.Dialog):

    def __init__(self, cellvalue):
        wx.Dialog.__init__(self, None, wx.ID_ANY, "Find Where Used",
                           style=wx.DEFAULT_DIALOG_STYLE)
        """
        self.SetBackgroundColour(Colour(200, 222, 40))
        self.SetForegroundColour(Colour(7, 0, 70))
        """
        self.caption = _("Please select what you want to check for usage")
        variables = set(variablematcher.find_variable_basenames(cellvalue))
        self.choices = [(False, cellvalue)] + [(True, v) for v in variables]
        self.choices_string = [_("Complete cell content")] + \
                              [_("Variable ") + var.replace("&", "&&") for var
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
        sizer.Add(wx.Button(self, wx.ID_OK, label=_("Search")),
                  0, wx.ALL | wx.ALIGN_CENTER, 5)
        big_sizer = wx.BoxSizer(wx.VERTICAL)
        big_sizer.Add(sizer, 0, wx.ALL, 10)
        self.SetSizer(big_sizer)
        self.Fit()
        self.CenterOnParent()

    def GetStringSelection(self):
        return self.choices[self.radiobox_choices.GetSelection()]
