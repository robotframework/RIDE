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
    ContentType.STRING: 'black'
    }

    BACKGROUND_COLORS = {
    CellType.UNKNOWN: 'white'
    }

    def __init__(self, grid, controller):
        self._grid = grid
        self._controller = controller

    def colorize(self, row, col, value, previous):
        self._colorize_cell(row, col, value)
        self._handle_comment_or_uncomment(row, col, value, previous)

    def _colorize_cell(self, row, col, value):
        cell_info = self._controller.get_cell_info(row, col)
        text_color = self.TEXT_COLORS[cell_info.content_type]
        self._grid.SetCellTextColour(row, col, text_color)
        background_color = self.BACKGROUND_COLORS[cell_info.cell_type]
        self._grid.SetCellBackgroundColour(row, col, background_color)

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
