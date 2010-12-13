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
from robotide import utils


class Colorizer(object):
    """Colorizes cells in the keyword editor"""

    ERROR_COLOR = '#FF9385'

    TEXT_COLORS = {
    ContentType.COMMENTED: 'firebrick',
    ContentType.USER_KEYWORD: 'blue',
    ContentType.LIBRARY_KEYWORD: 'blue',
    ContentType.VARIABLE: 'forest green',
    ContentType.STRING: 'black',
    ContentType.EMPTY: 'black'
    }

    BACKGROUND_COLORS = {
    CellType.HIGHLIGHTED: '#FFFF77',
    CellType.UNKNOWN: '#FFFFFF',
    CellType.MANDATORY: '#F4FFFF',
    CellType.MANDATORY_EMPTY: '#C0C0C0',
    CellType.OPTIONAL: '#F5F5F5'
    }

    def __init__(self, grid, controller):
        self._grid = grid
        self._controller = controller

    def colorize(self):
        selection_matcher = self._get_selection_matcher()
        for row in range(0, self._grid.NumberRows):
            for col in range(0, self._grid.NumberCols):
                self._colorize_cell(row, col, selection_matcher)

    def _get_selection_matcher(self):
        cells = self._grid.get_selected_content()
        if len(cells) != 1 or len(cells[0]) != 1:
            return lambda x: False
        cell_content = utils.normalize(cells[0][0])
        if not cell_content:
            return lambda x: False
        def matches(other):
            return cell_content==utils.normalize(other)
        return matches

    def _colorize_cell(self, row, col, selection_matcher):
        cell_info = self._controller.get_cell_info(row, col, selection_matcher)
        if cell_info is None:
            return
        self._grid.SetCellTextColour(row, col, self._get_text_color(cell_info))
        self._grid.SetCellBackgroundColour(row, col, self._get_background_color(cell_info))

    def _get_text_color(self, cell_info):
        return self.TEXT_COLORS[cell_info.content_type]

    def _get_background_color(self, cell_info):
        if cell_info.has_error():
            return self.ERROR_COLOR
        return self.BACKGROUND_COLORS[cell_info.cell_type]

