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

import re

from robotide.publish import RideGridCellChanged
from robotide.pluginapi import Plugin
from robotide.controller.cellinfo import CellInfo, ContentType, CellType


class Colorizer(Plugin):
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

    def __init__(self, application):
        Plugin.__init__(self, application)

    def enable(self):
        self.subscribe(self.OnCellChanged, RideGridCellChanged)

    def disable(self):
        self.unsubscribe(self.OnCellChanged, RideGridCellChanged)

    def OnCellChanged(self, event):
        row, col = event.cell
        self._colorize_cell(event.grid, row, col, event.value)
        self._handle_comment_or_uncomment(event.grid, row, col, event.value,
                                          event.previous)

    def _colorize_cell(self, grid, row, col, value):
        cell_info = self._get_cell_info(grid, row, value)
        text_color = self.TEXT_COLORS[cell_info.content_type]
        grid.SetCellTextColour(row, col, text_color)
        background_color = self.BACKGROUND_COLORS[cell_info.cell_type]
        grid.SetCellBackgroundColour(row, col, background_color)

    def _get_cell_info(self, grid, row, value):
        if self._is_commented(grid, row):
            return CellInfo(ContentType.COMMENTED, CellType.UNKNOWN)
        if self._is_variable(value):
            return CellInfo(ContentType.VARIABLE, CellType.UNKNOWN)
        if self.is_user_keyword(value):
            return CellInfo(ContentType.USER_KEYWORD, CellType.UNKNOWN)
        if self.is_library_keyword(value):
            return CellInfo(ContentType.LIBRARY_KEYWORD, CellType.UNKNOWN)
        return CellInfo(ContentType.STRING, CellType.UNKNOWN)

    def _is_variable(self, value):
        return re.match('[\$\@]{.*?}=?', value)

    def _is_commented(self, grid, row):
        for i in range(grid.NumberCols):
            cell_val = grid.GetCellValue(row, i).strip().lower()
            if i == 0 and cell_val == "comment":
                return True
            if cell_val.startswith('#'):
                return True
        return False

    def _handle_comment_or_uncomment(self, grid, row, col, value, previous):
        """If a row is (un)commented, that row need to be re-colorized"""
        value, previous = value.strip().lower(), previous.strip().lower()
        if not self._may_be_comment_or_uncomment(col, value, previous):
            return
        if value == "comment" or previous == 'comment':
            for col in range(0, grid.NumberCols):
                self._colorize_cell(grid, row, col, value)

    def _may_be_comment_or_uncomment(self, col, value, previous):
        return col == 0 and value != previous
