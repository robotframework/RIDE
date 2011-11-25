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


class TableWriter(object):

    def __init__(self,
                 output,
                 cell_separator,
                 line_separator,
                 line_prefix='',
                 line_postfix=''):
        self._output = output
        self._cell_separator = cell_separator
        self._line_separator = line_separator
        self._line_prefix = line_prefix
        self._line_postfix = line_postfix
        self._headers = None
        self._data = []

    def add_headers(self, headers):
        self._headers = headers

    def add_row(self, row):
        self._data += [row]

    def write(self):
        separators = self._compute_cell_separators()
        for row, col_separators in zip([self._headers]+self._data, separators):
            if row == []:
                self._output.write(self._line_separator)
            else:
                self._write_row(row, col_separators)

    def _write_row(self, row, col_separators):
        if self._line_prefix:
            self._output.write(self._line_prefix)
        while col_separators and len(row) > 1:
            self._output.write(row.pop(0))
            self._output.write(col_separators.pop(0))
        if row:
            self._output.write(row.pop(0))
        self._output.write(self._line_postfix+self._line_separator)

    def _compute_cell_separators(self):
        if len(self._headers) < 2:
            return [[self._cell_separator for _ in range(len(row)-1)] for row in [self._headers]+self._data]
        lengths = self._max_column_item_lengths_ignore_rows_with_one_column()
        separators = []
        for row in [self._headers]+self._data:
            col_separators = []
            for i, col in enumerate(row[:-1]):
                col_separators += [' '*(lengths[i]-len(col))+self._cell_separator]
            separators += [col_separators]
        return separators


    def _max_column_item_lengths_ignore_rows_with_one_column(self):
        lengths = {}
        for row in [self._headers]+self._data:
            if len(row) < 2:
                continue
            for i, item in enumerate(row):
                lengths[i] = max(lengths.get(i, 0), len(item))
        return lengths

    def _unify_first_two_columns_with(self, cell_separator):
        for row in self._data:
            if len(row) > 1:
                row[0] = row[0]+cell_separator+row[1]
                row.pop(1)
