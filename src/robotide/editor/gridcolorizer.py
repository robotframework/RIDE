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

from robotide.controller.cellinfo import ContentType, CellType
# this import fails in HUDSON
# from wxPython._gdi import wxFONTWEIGHT_BOLD, wxFONTWEIGHT_NORMAL
wxFONTWEIGHT_BOLD = 92
wxFONTWEIGHT_NORMAL = 90

class Colorizer(object):
    # FIXME: Colors from settings
    """Colorizes cells in the keyword editor"""

    ERROR_COLOR = '#FF9385'
    HIGHLIGHTED_COLOR = '#FFFF77'

    TEXT_COLORS = {
        ContentType.USER_KEYWORD: 'blue',
        ContentType.LIBRARY_KEYWORD: 'blue',
        ContentType.VARIABLE: 'forest green',
        ContentType.COMMENTED: 'firebrick',
        ContentType.STRING: 'black',
        ContentType.EMPTY: 'black',
    }

    BACKGROUND_COLORS = {
        CellType.ASSIGN: '#FFFFFF',
        CellType.KEYWORD: '#FFFFFF',
        CellType.MANDATORY: '#FFFFFF',
        CellType.OPTIONAL: '#F5F5F5',
        CellType.MUST_BE_EMPTY: '#C0C0C0',
        CellType.UNKNOWN: '#FFFFFF',
    }

    def __init__(self, grid, controller):
        self._grid = grid
        self._controller = controller

    def colorize(self, selection_content):
        for row in range(0, self._grid.NumberRows):
            for col in range(0, self._grid.NumberCols):
                self._colorize_cell(row, col, selection_content)

    def _colorize_cell(self, row, col, selection_content):
        cell_info = self._controller.get_cell_info(row, col)
        if cell_info is None:
            return
        self._grid.SetCellTextColour(row, col, self._get_text_color(cell_info))
        self._grid.SetCellBackgroundColour(row, col, self._get_background_color(cell_info, selection_content))
        self._grid.SetCellFont(row, col, self._get_cell_font(row, col, cell_info))

    def _get_text_color(self, cell_info):
        return self.TEXT_COLORS[cell_info.content_type]

    def _get_background_color(self, cell_info, selection_content):
        if cell_info.matches(selection_content):
            return self.HIGHLIGHTED_COLOR
        if cell_info.has_error():
            return self.ERROR_COLOR
        return self.BACKGROUND_COLORS[cell_info.cell_type]

    def _get_cell_font(self, row, col, cell_info):
        font = self._grid.GetCellFont(row, col)
        font.SetWeight(self._get_weight(cell_info))
        return font

    def _get_weight(self, cell_info):
        if cell_info.cell_type == CellType.KEYWORD:
            return wxFONTWEIGHT_BOLD
        return wxFONTWEIGHT_NORMAL
