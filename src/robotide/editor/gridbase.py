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
import wx
from wx import grid, Colour

from .clipboard import ClipboardHandler
from ..context import IS_WINDOWS
from ..utils import unescape_newlines_and_whitespaces
from ..widgets import PopupCreator, PopupMenuItems

_ = wx.GetTranslation  # To keep linter/code analyser happy
builtins.__dict__['_'] = wx.GetTranslation


class GridEditor(grid.Grid):
    _col_add_threshold = 6
    _popup_items = []

    _popup_items_nt = []

    def __init__(self, parent, num_rows, num_cols, popup_creator=None):
        grid.Grid.__init__(self, parent)
        try:
            self.settings = parent.plugin.global_settings['Grid']
            self.general_settings = parent.plugin.global_settings['General']
        except AttributeError:
            from ..preferences import RideSettings
            _settings = RideSettings()
            self.general_settings = _settings['General']
            self.settings = _settings['Grid']
        self.filter_newlines = self.settings.get("filter newlines", True)
        self.color_background = self.settings['background unknown']
        self.color_foreground = self.settings['text empty']
        self.color_background_help = self.general_settings['background help']
        self.color_foreground_text = self.general_settings['foreground text']
        self.color_secondary_background = self.general_settings['secondary background']
        self.color_secondary_foreground = self.general_settings['secondary foreground']

        self._bind_to_events()
        self.selection = _GridSelection(self)
        self._clipboard_handler = ClipboardHandler(self)
        self._history = _GridState()
        self.CreateGrid(int(num_rows), int(num_cols))
        self.SetDefaultCellBackgroundColour(Colour(self.color_background))
        self.SetDefaultCellTextColour(Colour(self.color_foreground))
        self.GetGridColLabelWindow().SetBackgroundColour(Colour(self.color_secondary_background))
        self.GetGridColLabelWindow().SetForegroundColour(Colour(self.color_secondary_foreground))
        self.GetGridRowLabelWindow().SetBackgroundColour(Colour(self.color_secondary_background))
        self.GetGridRowLabelWindow().SetForegroundColour(Colour(self.color_secondary_foreground))
        self.SetLabelBackgroundColour(Colour(self.color_secondary_background))
        self.SetLabelTextColour(Colour(self.color_secondary_foreground))
        self._popup_creator = popup_creator or PopupCreator()
        """
        DEBUG: This block adds aditional scrollbars in mains Grid Editor, making hard to focus on cells keeping the 
               row numbers visible.
        if hasattr(parent, 'SetupScrolling'):
            parent.SetupScrolling(scrollToTop=True, scrollIntoView=True)
            print("DEBUG: GridBase init at PARENT SetupScrolling\n")
        elif
        """
        if hasattr(self, 'SetupScrolling'):
            self.SetupScrolling(scrollToTop=True, scrollIntoView=True)
            # print("DEBUG: GridBase init at SELF SetupScrolling\n")
        # else:
        #     print("DEBUG: GridBase init NO SetupScrolling\n")

    def _bind_to_events(self):
        self.Bind(grid.EVT_GRID_SELECT_CELL, self.on_select_cell)
        self.Bind(grid.EVT_GRID_RANGE_SELECT, self.on_range_select)
        self.Bind(grid.EVT_GRID_CELL_RIGHT_CLICK, self.on_cell_right_click)

    def register_context_menu_hook(self, cb):
        self._popup_creator.add_hook(cb)

    def unregister_context_menu_hook(self, cb):
        self._popup_creator.remove_hook(cb)

    def write_cell(self, row, col, value, update_history=True):
        if update_history:
            self._update_history()
        self._expand_if_necessary(row, col)
        if self.filter_newlines:
            # unescape \n to support multi lines display in grid cells
            value = unescape_newlines_and_whitespaces(value)
        self.SetCellValue(row, col, value)

    def _expand_if_necessary(self, row, col):
        # Changed col and row fill because of blank spacing not changing color
        # print(f"DEBUG: GridEditor ENTER_expand_if_necessary row={row}, col={col}")
        while self.NumberRows <= max(1, row+1, 10-row):  # DEBUG 25 makes slower rendering
            self.AppendRows(1)
        while self.NumberCols <= max(1, col+1, 10-col):  # DEBUG 40 makes slower rendering
            self.AppendCols(max(1, self._col_add_threshold))  # DEBUG: was infinite when value was 0

    def has_focus(self):
        return self.FindFocus() == self

    def _update_history(self):
        self._history.change(self._get_all_content())

    def _get_all_content(self):
        return self._get_block_content(range(self.NumberRows),
                                       range(self.NumberCols))

    @property
    def cell_under_cursor(self):
        x, y = self.ScreenToClient(wx.GetMousePosition())
        x -= self.RowLabelSize
        y -= self.GetColLabelSize()
        return self.XYToCell(*self.CalcUnscrolledPosition(x, y))

    def select(self, row, column):
        self.SelectBlock(row, column, row, column)
        self.SetGridCursor(row, column)
        self.MakeCellVisible(row, column)

    def copy(self):
        print("DEBUG: GridBase copy() called\n")
        self._clipboard_handler.clear()
        data = self._clipboard_handler.clipboard_content()
        print(f"DEBUG: GridBase copy() clipboard_content =={data}\n")
        self._clipboard_handler.copy()

    def cut(self):
        self._update_history()
        self._clipboard_handler.clear()
        self._clipboard_handler.cut()
        self._clear_selected_cells()

    def _clear_selected_cells(self):
        self.BeginBatch()
        for row, col in self.selection.cells():
            self.write_cell(row, col, '')  # , update_history=False)
        self.EndBatch()

    def paste(self):
        self._update_history()
        self._clipboard_handler.paste()

    def delete(self):
        self._update_history()
        _iscelleditcontrolshown = self.IsCellEditControlShown()
        if _iscelleditcontrolshown:
            if IS_WINDOWS:
                self._delete_from_cell_editor()
        else:
            self._clear_selected_cells()

    def _delete_from_cell_editor(self):
        editor = self.get_cell_edit_control()
        start, end = editor.Selection
        if start == end:
            end += 1
        editor.Remove(start, end)

    def _is_whole_row_selection(self):
        return self.SelectedRows

    def _is_whole_column_selection(self):
        return self.SelectedCols

    def get_cell_edit_control(self):
        return self.GetCellEditor(*self.selection.cell).GetControl()

    def get_selected_content(self):
        return self._get_block_content(self.selection.rows(), self.selection.cols())

    def get_single_selection_content(self):
        cells = self.get_selected_content()
        if len(cells) != 1 or len(cells[0]) != 1:
            return None
        return cells[0][0]

    def _current_cell_value(self):
        return self.GetCellValue(*self.selection.cell)

    def _get_block_content(self, row_range, col_range):
        try:
            content = [[self.GetCellValue(row, col) for col in col_range] for row in row_range]
        except RuntimeError:
            return []
        return content

    @staticmethod
    def _strip_trailing_empty_cells(rowdata):
        while rowdata and not rowdata[-1]:
            rowdata.pop()
        return rowdata

    def undo(self):
        prev_data = self._history.back()
        if prev_data:
            self.ClearGrid()
            self._write_data(prev_data, update_history=False)

    def _write_data(self, data, update_history=True):
        self.BeginBatch()
        for row_index, row_data in enumerate(data):
            for col_index, cell_value in enumerate(row_data):
                self.write_cell(row_index, col_index, cell_value, update_history)
        self.EndBatch()

    def on_select_cell(self, event):
        if self._is_whole_row_selection() or self._is_whole_column_selection():
            self.SelectBlock(self.selection.topleft.row, self.selection.topleft.col,
                             self.selection.bottomright.row, self.selection.bottomright.col,
                             addToSelected=True)
        else:
            self.selection.set_from_single_selection(event)
        event.Skip()

    def on_range_select(self, event):
        if not event.Selecting():
            self.selection.clear()
            return
        if event.ControlDown():
            self.SetGridCursor(event.TopRow, event.LeftCol)
            self.SelectBlock(event.TopRow, event.LeftCol,
                             event.BottomRow, event.RightCol, addToSelected=False)
        else:
            self.selection.set_from_range_selection(self, event)
            self._ensure_selected_row_is_visible(event.BottomRow)

    def _ensure_selected_row_is_visible(self, bottom_row):
        if not self.IsVisible(bottom_row, 0) and bottom_row < self.NumberRows and \
                self._is_whole_row_selection():
            self.MakeCellVisible(bottom_row, 0)

    def on_cell_right_click(self, event):
        if hasattr(event, 'Row') and hasattr(event, 'Col'):
            if (event.Row, event.Col) not in self.selection.cells():
                self.select(event.Row, event.Col)
                self.selection.set_from_single_selection(event)
        self._popup_creator.show(self, PopupMenuItems(self, self._popup_items, self._popup_items_nt),
                                 self.get_selected_content())

    # DEBUG: This code is overriden at fieldeditors
    def on_insert_cells(self, event):
        self._insert_or_delete_cells(self._insert_cells, event)

    # DEBUG:This code is overriden at fieldeditors
    def on_delete_cells(self, event):
        # print("DEBUG delete cells %s" % event)
        self._insert_or_delete_cells(self._delete_cells, event)

    def _insert_or_delete_cells(self, action, event):
        self._update_history()
        # print("DEBUG insert or delete selected %s" % self.selection.rows())
        for index in self.selection.rows():
            data = action(self._row_data(index))
            self._write_row(index, data)
        self._refresh_layout()
        event.Skip()

    def _insert_cells(self, data):
        cols = self.selection.cols()
        left = right = cols[0]
        data[left:right] = [''] * len(cols)
        return self._strip_trailing_empty_cells(data)

    def _delete_cells(self, data):
        cols = self.selection.cols()
        # print("DEBUG delete cols selected %s" % cols)
        left, right = cols[0], cols[-1]   # + 1  # DEBUG removed extra cell
        # print("DEBUG delete left, right (%d,%d) values %s" % (left, right, data[left:right]))
        data[left:right] = []
        return data + [''] * len(cols)

    def _row_data(self, row):
        return [self.GetCellValue(row, col) for col in range(self.NumberCols)]

    def _write_row(self, row, data):
        for col, value in enumerate(data):
            self.write_cell(row, col, value, update_history=False)

    def _refresh_layout(self):
        self.SetFocus()
        self.SetGridCursor(*self.selection.cell)
        self.GetParent().Sizer.Layout()


# DEBUG: refactor this internal state away if possible
class _GridSelection(object):
    cell = property(lambda self: (self.topleft.row, self.topleft.col))

    def __init__(self, gridd):
        self._set((0, 0))
        self._grid = gridd

    def _set(self, topleft, bottomright=None):
        self.topleft = _Cell(topleft[0], topleft[1])
        self.bottomright = self._count_bottomright(topleft, bottomright)

    def _count_bottomright(self, topleft, bottomright):
        if not bottomright:
            return _Cell(topleft[0], topleft[1])
        return _Cell(min(self._grid.NumberRows - 1, bottomright[0]),
                     min(self._grid.NumberCols - 1, bottomright[1]))

    def set_from_single_selection(self, event):
        self._set((event.Row, event.Col))

    def set_from_range_selection(self, gridd, event):
        self._set(*self._get_bounding_coordinates(gridd, event))

    def clear(self):
        selection = (self._grid.GetGridCursorRow(), self._grid.GetGridCursorCol())
        self._set(selection)

    @staticmethod
    def _get_bounding_coordinates(gridd, event):
        whole_row_selection = sorted(gridd.SelectedRows)
        if whole_row_selection:
            return (whole_row_selection[0], 0), \
                   (whole_row_selection[-1], gridd.NumberCols - 1)
        return (event.TopLeftCoords.Row, event.TopLeftCoords.Col), \
               (event.BottomRightCoords.Row, event.BottomRightCoords.Col)

    def rows(self):
        """Returns a list containing indices of rows currently selected."""
        return range(self.topleft.row, self.bottomright.row + 1)

    def cols(self):
        """Returns a list containing indices of columns currently selected."""
        return range(self.topleft.col, self.bottomright.col + 1)

    def cells(self):
        """Return selected cells as a list of tuples (row, column)."""
        return [(row, col) for col in self.cols()
                for row in self.rows()]


class _Cell(object):

    def __init__(self, row, col):
        self.row = row
        self.col = col

    def __iter__(self):
        for item in self.row, self.col:
            yield item


class _GridState(object):

    def __init__(self):
        self._back = []
        self._forward = []

    def change(self, state):
        if not self._back or state != self._back[-1]:
            self._back.append(state)
            self._forward = []

    def back(self):
        if not self._back:
            return None
        self._forward.append(self._back.pop())
        return self._forward[-1]

    def forward(self):
        if not self._forward:
            return None
        state = self._forward.pop()
        self._back.append(state)
        return state
