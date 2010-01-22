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


class Colorizer(Plugin):
    """Colorizes cells in the keyword editor"""

    def __init__(self, application):
        settings  = {'comment_fg': 'firebrick', 'user_keyword_fg': 'blue',
                     'library_keyword_fg': 'blue', 'variable_fg':'forest green',
                     'default_fg':'black'}
        Plugin.__init__(self, application, default_settings=settings)

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
        color = self._get_color(grid, row, value)
        grid.SetCellTextColour(row, col, color)

    def _get_color(self, grid, row, value):
        if self._is_user_keyword(value):
            return self.user_keyword_fg
        if self._is_library_keyword(value):
            return self.library_keyword_fg
        if self._is_variable(value):
            return self.variable_fg
        if self._is_commented(grid, row):
            return self.comment_fg
        return self.default_fg

    def _is_user_keyword(self, value):
        return self.get_selected_datafile().get_user_keyword(value) is not None

    def _is_library_keyword(self, value):
        return self.get_selected_datafile().is_library_keyword(value)

    def _is_variable(self, value):
        return re.match('[\$\@]{.*?}=?', value)

    def _is_commented(self, grid, row):
        return grid.GetCellValue(row, 0).strip().lower() == "comment"

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
