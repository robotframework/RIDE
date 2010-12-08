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


class Colorizer(object):
    """Colorizes cells in the keyword editor"""

    TEXT_COLORS = {
    ContentType.COMMENTED: 'firebrick',
    ContentType.USER_KEYWORD: 'blue',
    ContentType.LIBRARY_KEYWORD: 'blue',
    ContentType.VARIABLE: 'forest green',
    ContentType.STRING: 'black',
    ContentType.EMPTY: 'black'
    }

    BACKGROUND_COLORS = {
    CellType.UNKNOWN: '#FFFFFF',
    CellType.MANDATORY: '#FFFFFF',
    CellType.MANDATORY_EMPTY: '#C0C0C0',
    CellType.OPTIONAL: '#F5F5F5',
    'Error': '#FF9385'
    }

    def __init__(self, grid, controller):
        self._grid = grid
        self._controller = controller

    def colorize(self, row, col, value, previous):
        for c in range(0, self._grid.NumberCols):
            self._colorize_cell(row, c)
        self._handle_comment_or_uncomment(row, col, value, previous)

    def _colorize_cell(self, row, col):
        cell_info = self._controller.get_cell_info(row, col)
        self._grid.SetCellTextColour(row, col, self._get_text_color(cell_info))
        self._grid.SetCellBackgroundColour(row, col, self._get_background_color(cell_info))

    def _get_text_color(self, cell_info):
        return self.TEXT_COLORS[cell_info.content_type]

    def _get_background_color(self, cell_info):
        if cell_info.has_error():
            return self.BACKGROUND_COLORS['Error']
        return self.BACKGROUND_COLORS[cell_info.cell_type]

    def _handle_comment_or_uncomment(self, row, col, value, previous):
        """If a row is (un)commented, that row need to be re-colorized"""
        value, previous = value.strip().lower(), previous.strip().lower()
        if not self._may_be_comment_or_uncomment(col, value, previous):
            return
        if value == "comment" or previous == 'comment':
            for col in range(0, self._grid.NumberCols):
                self._colorize_cell(row, col, value)

    def _may_be_comment_or_uncomment(self, col, value, previous):
        return col == 0 and value != previous
