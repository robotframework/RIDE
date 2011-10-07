#  Copyright 2008-2011 Nokia Siemens Networks Oyj
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


class DataRow(object):
    _row_continuation_marker = '...'
    _whitespace_regexp = re.compile('\s+')
    _ye_olde_metadata_prefix = 'meta:'

    def __init__(self, cells):
        self.cells, self.comments = self._parse(cells)

    def _parse(self, row):
        data = []
        comments = []
        for cell in row:
            cell = self._collapse_whitespace(cell)
            if cell.startswith('#') and not comments:
                comments.append(cell[1:])
            elif comments:
                comments.append(cell)
            else:
                data.append(cell)
        return self._purge_empty_cells(data), self._purge_empty_cells(comments)

    def _collapse_whitespace(self, cell):
        return self._whitespace_regexp.sub(' ', cell).strip()

    def _purge_empty_cells(self, row):
        while row and not row[-1]:
            row.pop()
        # Cells with only a single backslash are considered empty
        return [cell if cell != '\\' else '' for cell in row]

    @property
    def head(self):
        return self.cells[0] if self.cells else None

    @property
    def _tail(self):
        return self.cells[1:] if self.cells else None

    @property
    def all(self):
        return self.cells

    @property
    def data(self):
        if self.is_continuing():
            index = self.cells.index(self._row_continuation_marker) + 1
            return self.cells[index:]
        return self.cells

    def dedent(self):
        datarow = DataRow([])
        datarow.cells = self._tail
        datarow.comments = self.comments
        return datarow

    def startswith(self, value):
        return self.head() == value

    def handle_old_style_metadata(self):
        if self._is_metadata_with_olde_prefix(self.head):
            self.cells = self._convert_to_new_style_metadata()

    def _is_metadata_with_olde_prefix(self, value):
        return value.lower().startswith(self._ye_olde_metadata_prefix)

    def _convert_to_new_style_metadata(self):
        return ['Metadata'] + [self.head.split(':', 1)[1].strip()] + self._tail

    def starts_for_loop(self):
        if self.head and self.head.startswith(':'):
            return self.head.replace(':', '').replace(' ', '').upper() == 'FOR'
        return False

    def starts_test_or_user_keyword_setting(self):
        head = self.head
        return head and head[0] == '[' and head[-1] == ']'

    def test_or_user_keyword_setting_name(self):
        return self.head[1:-1].strip()

    def is_indented(self):
        return self.head == ''

    def is_continuing(self):
        for cell in self.cells:
            if cell == self._row_continuation_marker:
                return True
            if cell:
                return False

    def is_commented(self):
        return bool(not self.cells and self.comments)

    def __nonzero__(self):
        return bool(self.cells or self.comments)
