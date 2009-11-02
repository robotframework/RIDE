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

from robotide import context
from plugin import Plugin


class Colorizer(Plugin):
    """Colorizes cells in the keyword editor"""

    def __init__(self, application):
        Plugin.__init__(self, application)
        self._frame = self.get_frame()
        self._notebook = self.get_notebook()
        self._settings = context.SETTINGS.add_section(self.name)
        self._settings.set_defaults(comment_fg="firebrick",
                                    keyword_fg='blue',
                                    variable_fg='forest green')

    def activate(self):
        self.subscribe(self.OnCellChanged,("core","grid","cell changed"))

    def deactivate(self):
        self.unsubscribe(self.OnCellChanged,("core","grid","cell changed"))

    def OnCellChanged(self, message):
        """Update the color of the cell whenever the content changes"""
        grid = message.data["grid"]
        row, col = message.data['cell']
        value = message.data["value"]
        previous = message.data["previous"]
        self._colorize_cell(grid, row, col, value)
        self._handle_comment_or_uncomment(grid, row, col, value, previous)

    def _colorize_cell(self, grid, row, col, value):
        color = self._get_color(grid, row, col, value)
        grid.SetCellTextColour(row, col, color)

    def _get_color(self, grid, row, col, value):
        if self._is_commented(grid, row):
            return self._settings["comment_fg"]
        if self._is_user_keyword(grid, value):
            return self._settings["keyword_fg"]
        if self._is_variable(value):
            return self._settings["variable_fg"]
        return 'black'

    def _is_variable(self, value):
        return re.match('[\$\@]{.*?}=?', value)

    def _is_user_keyword(self, grid, value):
        return grid._datafile.get_user_keyword(value) is not None

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
