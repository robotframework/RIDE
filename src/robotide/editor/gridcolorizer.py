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

from ..controller.cellinfo import CellType


# this import fails in HUDSON
# from wxPython._gdi import wxFONTWEIGHT_BOLD, wxFONTWEIGHT_NORMAL
# wxFONTWEIGHT_BOLD = 92
# wxFONTWEIGHT_NORMAL = 90
# DEBUG using wx.FONTWEIGHT_BOLD, wx.FONTWEIGHT_NORMAL


class Colorizer(object):

    def __init__(self, grid, controller):
        self._grid = grid
        self._controller = controller
        self._colors = ColorizationSettings(grid.settings)
        self._current_task_id = 0
        self._timer = None

    def close(self):
        self._grid = None

    def colorize(self, selection_content):
        self._current_task_id += 1
        if self._timer is None:
            self._timer = wx.CallLater(1, self._coloring_task, self._current_task_id, selection_content)
        else:
            self._timer.Restart(50, self._current_task_id, selection_content)

    def _coloring_task(self, task_index, selection_content, row=0, col=0):
        if task_index != self._current_task_id or self._grid is None:
            return
        if row >= self._grid.NumberRows:
            self._grid.ForceRefresh()
        elif col < self._grid.NumberCols:
            self._colorize_cell(row, col, selection_content)
            wx.CallAfter(self._coloring_task, task_index, selection_content, row, col+1)
        else:
            self._coloring_task(task_index, selection_content, row+1, 0)

    def _colorize_cell(self, row, col, selection_content):
        cell_info = self._controller.get_cell_info(row, col)
        if cell_info is None:
            self._set_default_colors(row, col)
            return
        self._grid.SetCellTextColour(row, col, self._get_text_color(cell_info))
        self._grid.SetCellBackgroundColour(row, col, self._get_background_color(cell_info, selection_content))
        self._grid.SetCellFont(row, col, self._get_cell_font(row, col, cell_info))

    def _set_default_colors(self, row, col):
        self._grid.SetCellTextColour(row, col, self._colors.DEFAULT_TEXT)
        self._grid.SetCellBackgroundColour(row, col, self._colors.DEFAULT_BACKGROUND)

    def _get_text_color(self, cell_info):
        return self._colors.get_text_color(cell_info.content_type)

    def _get_background_color(self, cell_info, selection_content):
        if cell_info.matches(selection_content):
            return self._colors.get_highlight_color()
        if cell_info.has_error():
            return self._colors.get_error_color()
        return self._colors.get_background_color(cell_info.cell_type)

    def _get_cell_font(self, row, col, cell_info):
        font = self._grid.GetCellFont(row, col)
        font.SetWeight(self._get_weight(cell_info))
        return font

    @staticmethod
    def _get_weight(cell_info):
        if cell_info.cell_type == CellType.KEYWORD:
            return wx.FONTWEIGHT_BOLD
        return wx.FONTWEIGHT_NORMAL


class ColorizationSettings(object):

    DEFAULT_TEXT = ''  # Colour('black')  # Colour(7, 0, 70)  # 'black'
    DEFAULT_BACKGROUND = ''  # 'light grey' # Colour('light grey')  # Colour(200, 222, 40)  # 'white'

    def __init__(self, settings=None):
        self._settings = settings

    def get_background_color(self, elem_type):
        if not self._settings:
            return self.DEFAULT_BACKGROUND
        return self._get(f'background {elem_type}')

    def get_text_color(self, elem_type):
        if not self._settings:
            return self.DEFAULT_TEXT
        return self._get(f'text {elem_type}')

    def get_highlight_color(self):
        return self.get_background_color('highlight')

    def get_error_color(self):
        return self.get_background_color('error')

    def _get(self, name):
        color_setting = name.lower().replace('_', ' ')
        if color_setting in self._settings:
            return self._settings[color_setting]
        else:
            return CellType.UNKNOWN
