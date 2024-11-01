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

import re

from multiprocessing import shared_memory
from robotide.lib.compat.parsing.language import get_headers_for
from .aligners import FirstColumnAligner, ColumnAligner, NullAligner
from .dataextractor import DataExtractor
from .rowsplitter import RowSplitter


class _DataFileFormatter(object):
    _whitespace = re.compile(r"\s{2,}")
    _split_multiline_doc = True
    language = None

    def __init__(self, column_count, split_multiline_doc=True, language=None):
        try:
            if not language:
                set_lang = shared_memory.ShareableList(name="language")
                self.language = [set_lang[0]]
            else:
                self.language = language
        except (AttributeError, FileNotFoundError):
            self.language = ['en']
        self._split_multiline_doc = split_multiline_doc
        # print(f"DEBUG: formatters.py _DataFileFormatter INIT call _splitter  {self._split_multiline_doc=}"
        #       f" {self.language=}")
        self._splitter = RowSplitter(column_count, self._split_multiline_doc, self.language)
        self._column_count = column_count
        self._extractor = DataExtractor(self._want_names_on_first_content_row)

    def _want_names_on_first_content_row(self, table, name):
        return True

    def empty_row_after(self, table):
        return self._format_row([], table)

    def format_header(self, table):
        header = self._format_row(table.header)
        # print(f"DEBUG: formatters.py _DataFileFormatter format_header header={header}")
        return self._format_header(header, table)

    def format_table(self, table):
        rows = self._extractor.rows_from_table(table)
        # if rows:
        #     print(f"DEBUG: writer formatters.py format_table after extractor table.type={table.type}")
        if rows and table.type == 'comments':
            # print(f"DEBUG: formatters.py format_table rows={[r for r in rows]}")
            return [r for r in rows]
        if self._should_split_rows(table) and table.type != 'comments':
            rows = self._split_rows(rows, table)
        return (self._format_row(r, table) for r in rows)

    def _should_split_rows(self, table):
        return not self._should_align_columns(table)

    def _split_rows(self, original_rows, table):
        # print(f"DEBUG: formatters.py _split_rows Printing rows for table={table.type}")
        # for original in original_rows:
        #     print(original)
        for original in original_rows:
            for split in self._splitter.split(original, table.type):
                yield split

    def _should_align_columns(self, table):
        return self._is_indented_table(table) and bool(table.header[1:])

    @staticmethod
    def _is_indented_table(table):
        return table is not None and table.type in ['test case', 'keyword']

    def _escape_consecutive_whitespace(self, row):
        return [self._whitespace.sub(self._whitespace_escaper,
                                     cell.replace('\n', ' ')) for cell in row]

    @staticmethod
    def _whitespace_escaper(match):
        return '\\'.join(match.group(0))

    def _format_row(self, row, table=None):
        raise NotImplementedError

    def _format_header(self, header, table):
        raise NotImplementedError


class TsvFormatter(_DataFileFormatter):

    def _format_header(self, header, table):
        return [self._format_header_cell(cell) for cell in header]

    @staticmethod
    def _format_header_cell(cell):
        return '*%s*' % cell if cell else ''

    def _format_row(self, row, table=None):
        return self._pad(self._escape(row))

    def _escape(self, row):
        return self._escape_consecutive_whitespace(self._escape_tabs(row))

    @staticmethod
    def _escape_tabs(row):
        return [c.replace('\t', '\\t') for c in row]

    def _pad(self, row):
        row = [cell.replace('\n', ' ') for cell in row]
        return row + [''] * (self._column_count - len(row))


def translate_header(header: str, language=None) -> str:
    if not language:
        return header
    tr_header = list(get_headers_for(language, header, lowercase=False))
    if len(tr_header) > 1:
        # print(f"DEBUG: formatters.py translate_header  header={header} language={language}"
        #       f" before pop tr_header={tr_header}")
        tr_header.pop(tr_header.index(header))
    tr_header = tr_header[0]
    # print(f"DEBUG: formatters.py translate_header  header={tr_header}")
    return tr_header


class TxtFormatter(_DataFileFormatter):
    _test_or_keyword_name_width = 18
    _setting_and_variable_name_width = 14

    def __init__(self, column_count, language=None):
        _DataFileFormatter.__init__(self, column_count=column_count, split_multiline_doc=True, language=language)

    def _format_row(self, row, table=None):
        # if table and table.type == 'setting':
        #     print(f"DEBUG: formatters.py format_row ENTER setting row={row}")
        if table and table.type == 'comments':
            return row
        # Unit tests failing here with row[0]==None
        if row and row[0] is None:
            row[0] = ' '
        row = self._escape(row)
        aligner = self._aligner_for(table)
        return aligner.align_row(row)

    def _aligner_for(self, table):
        if table and table.type in ['setting', 'variable', 'comments']:
            return FirstColumnAligner(self._setting_and_variable_name_width)
        if self._should_align_columns(table):
            return ColumnAligner(self._test_or_keyword_name_width, table)
        return NullAligner()

    def _format_header(self, header, table):
        # print(f"DEBUG: RFLib writer formaters.py TxtFormatter _format_header headers={header} table={table}")
        header = ['*** %s ***' % translate_header(header[0])] + header[1:]
        aligner = self._aligner_for(table)
        return aligner.align_row(header)

    def _want_names_on_first_content_row(self, table, name):
        return self._should_align_columns(table) and \
                len(name) <= self._test_or_keyword_name_width

    def _escape(self, row):
        if not row:
            return row
        return list(self._escape_cells(self._escape_consecutive_whitespace(row)))

    def _escape_cells(self, row):
        escape = False
        for cell in row:
            if cell:
                escape = True
            elif escape:
                cell = '\\'
            yield cell


class PipeFormatter(TxtFormatter):

    def _escape_cells(self, row):
        return [self._escape_empty(self._escape_pipes(cell)) for cell in row]

    @staticmethod
    def _escape_empty(cell):
        return cell or '  '

    @staticmethod
    def _escape_pipes(cell):
        if ' | ' in cell:
            cell = cell.replace(' | ', ' \\| ')
        if cell.startswith('| '):
            cell = '\\' + cell
        if cell.endswith(' |'):
            cell = cell[:-1] + '\\|'
        return cell
