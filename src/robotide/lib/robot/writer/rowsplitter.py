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

import itertools
from multiprocessing import shared_memory
from robotide.lib.compat.parsing.language import get_settings_for


class RowSplitter(object):
    _comment_mark = '#'
    _empty_cell_escape = ''  # '${EMPTY}'
    _line_continuation = '...'
    setting_table = 'setting'
    _indented_tables = ('test case', 'keyword')
    _split_from = ('ELSE', 'ELSE IF', 'AND', 'VAR')

    def __init__(self, cols=8, split_multiline_doc=False, split_multiline_var=True, language=None):
        self._cols = cols
        self._split_multiline_doc = split_multiline_doc
        self._split_multiline_var = split_multiline_var
        try:
            if not language:
                set_lang = shared_memory.ShareableList(name="language")
                self._language = [set_lang[0]]
            else:
                self._language = language
        except (AttributeError, FileNotFoundError):
            self._language = ['en']
        self._table_type = None

    def split(self, row, table_type):
        self._table_type = table_type
        if not row:
            return self._split_empty_row()
        indent = self._get_indent(row, table_type)
        if self._split_multiline_doc and self._is_doc_row(row, table_type):
            return self._split_doc_row(row, indent)
        return self._split_row(row, indent)

    @staticmethod
    def _split_empty_row():
        yield []

    def _get_indent(self, row, table_type):
        indent = self._get_first_non_empty_index(row)
        # print(f"DEBUG: rowsplitter.py RowSplitter _get_indent indent={indent} row={row} ")
        min_indent = 1 if table_type in self._indented_tables else 0
        return max(indent, min_indent)

    @staticmethod
    def _get_first_non_empty_index(row, indented=False):
        ignore = ['', '...'] if indented else ['']
        return len(list(itertools.takewhile(lambda x: x in ignore, row)))

    def _is_doc_row(self, row, table_type):
        if table_type == self.setting_table:
            # print(f"DEBUG: writer.rowsplitter.py RowSplitter _is_doc_row in setting {self._language=}"
            #       f"\n row={row}")
            return len(row) > 1 and row[0] in get_settings_for(self._language, ('Documentation',))
        if table_type in self._indented_tables:
            return len(row) > 2 and row[1].strip('[]') in get_settings_for(self._language, ('Documentation',))
        return False

    def _split_doc_row(self, row, indent):
        first, rest = self._split_doc(row[indent+1])
        yield row[:indent+1] + [first] + row[indent+2:]
        while rest:
            current, rest = self._split_doc(rest)
            row = [current] if current else []
            yield self._continue_row(row, indent)

    @staticmethod
    def _split_doc(doc):
        if '\\n' not in doc:
            return doc, ''
        if '\\n ' in doc:
            doc = doc.replace('\\n ', '\\n')
        return doc.split('\\n', 1)

    def _split_row(self, row, indent):
        if self._table_type == 'variable' and self._split_multiline_var:
            # print(f"DEBUG: rowsplitter.py RowSplitter _split_row tabel Variable row={row}")
            split_at = self._cols
        else:
            split_at = None
        while row:
            current, row = self._split(row, forced_index=split_at)
            yield self._escape_last_cell_if_empty(current)
            if row:
                row = self._continue_row(row, indent)

    def _split(self, data, forced_index=None):
        if not forced_index:
            index = min(self._get_possible_split_indices(data))
        else:
            index = forced_index if len(data) > forced_index else min(self._get_possible_split_indices(data))
        current, rest = data[:index], data[index:]
        rest = self._comment_rest_if_needed(current, rest)
        return current, rest

    def _get_possible_split_indices(self, data):
        min_index = self._get_first_non_empty_index(data, indented=True) + 1
        if min_index >= 1 and data[min_index-1].startswith('['):  # Special cases of [Arguments], [Teardown], e.t.c.
            cols = self._cols + 20  # big number
        else:
            cols = self._cols
        for marker in self._split_from:
            if marker in data[min_index:]:
                yield data[min_index:].index(marker) + min_index
        yield cols

    def _comment_rest_if_needed(self, current, rest):
        if rest and any(c.startswith(self._comment_mark) for c in current) \
                and not rest[0].startswith(self._comment_mark):
            rest = [self._comment_mark + ' ' + rest[0]] + rest[1:]
        return rest

    def _escape_last_cell_if_empty(self, row):
        if row and not row[-1].strip():
            row = row[:-1] + [self._empty_cell_escape]
        return row

    def _continue_row(self, row, indent):
        row = [self._line_continuation] + row
        if indent + 1 < self._cols:
            row = [''] * indent + row
        return row
