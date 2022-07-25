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

from robotide.lib.robot.output import LOGGER
from robotide.lib.robot.utils import py2to3


@py2to3
class DataRow(object):
    _row_continuation_marker = '...'

    def __init__(self, cells, source=None):
        self.source = source
        if cells:
            self.cells, self.comments = self._parse(cells)
            # print(f"DEBUG: DataRow init cells and comments cells={self.cells} + {self.comments} \n")
        else:
            self.cells = []
            self.comments = []

    def _parse(self, row):
        data = []
        comments = []
        # print(f"DEBUG: datarow enter _parse row={row}\n")
        for cell in row:
            # print(f"DEBUG: datarow before clean cell={cell}")
            cell = self._collapse_whitespace(cell)
            # print(f"DEBUG: datarow after clean cell={cell}")
            if cell and cell[0] == '#' or comments:
                comments.append(cell)
            else:
                data.append(cell)
        if self._row_continuation_marker in data and self.source:
            self._deprecate_escaped_cells_before_continuation(data)
        return self._purge_empty_cells(data), comments  # DEBUG don't self._purge_empty_cells(comments)

    def _collapse_whitespace(self, cell):
        if cell.startswith('#'):
            return cell
        return ' '.join(cell.split())

    def _deprecate_escaped_cells_before_continuation(self, data):
        index = data.index(self._row_continuation_marker)
        if any(cell == '\\' for cell in data[:index]):
            LOGGER.warn("Error in file '%s': Escaping empty cells with "
                        "'\\' before line continuation marker '...' is "
                        "deprecated. Remove escaping before Robot "
                        "Framework 3.2." % self.source)

    def _purge_empty_cells(self, row):
        while row and not row[-1]:
            row.pop()
        # Cells with only a single backslash are considered empty
        return [cell if cell != '\\' else '' for cell in row]

    @property
    def first_non_empty_cell(self):
        # print(f"DEBUG: datarow enter _first_non_empty_cell")
        # if self.cells:
        #    print(f"DEBUG: datarow _first_non_empty_cell: {self.cells[:]}")
        index = 0
        while index < len(self.cells) and self.cells[index] == '':
            index += 1
        # print(f"DEBUG: datarow RETURNING  _first_non_empty_cell index ={index}")
        return index  # if index < len(self.cells) else index - 1

    @property
    def head(self):
        # print(f"DEBUG: datarow head={self.cells[:] if self.cells else 'NONE!!!'}")
        # return self.cells[self.first_non_empty_cell] if self.cells else ''
        return self.cells[0] if self.cells else ''

    @property
    def tail(self):
        # print(f"DEBUG: datarow tail={self.cells[self.first_non_empty_cell:]}")
        # We want to keep indentation, so we only remove first empty cell
        # index = 1 if len(self.cells) > 1 else 0
        # return self.cells[self.first_non_empty_cell:]
        return self.cells[1:]

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
        import inspect
        datarow = DataRow([])
        datarow.cells = self.tail
        datarow.comments = self.comments
        stack = inspect.stack()
        the_class = stack[1][0].f_locals["self"].__class__.__name__
        the_method = stack[1][0].f_code.co_name
        # print("DEBUG: datarow dedent called by {}.{}()".format(the_class, the_method))
        # print(f"DEBUG: datarow dedent={datarow.all[:]}")
        return datarow

    def starts_for_loop(self):
        # head = self.head
        head = self.cells[self.first_non_empty_cell]
        if not self.head:
            self.__setattr__(self.head, head)
            # print(f"DEBUG: datarow starts_for_loop NEW CALCULATION head={head}")
        # else:
        #    head = self.head
        # print(f"DEBUG: datarow starts_for_loop head={head}")
        if head.startswith(':'):
            return head.replace(':', '').replace(' ', '').upper() == 'FOR'
        return head == 'FOR'

    def starts_test_or_user_keyword_setting(self):
        head = self.head
        # print(f"DEBUG: datarow CALLING starts_test_or_user_keyword_setting head={head}")
        return head and head[0] == '[' and head[-1] == ']'

    def test_or_user_keyword_setting_name(self):
        return self.head[1:-1].strip()

    def is_indented(self):
        return self.head == ''
        # return self.first_non_empty_cell > 0

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
