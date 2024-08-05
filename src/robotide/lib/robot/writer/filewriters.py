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

import builtins
try:
    import csv
except ImportError:
    # csv module is missing from IronPython < 2.7.1
    csv = None

import wx

from robotide.lib.robot.utils import HtmlWriter, PY2

from .formatters import TsvFormatter, TxtFormatter, PipeFormatter
from .htmlformatter import HtmlFormatter
from .htmltemplate import TEMPLATE_START, TEMPLATE_END

_ = wx.GetTranslation  # To keep linter/code analyser happy
builtins.__dict__['_'] = wx.GetTranslation


def table_sorter(tables: list) -> list:
    sorted_tables = []
    prev_tab_line = 0
    for idx, tab in enumerate(tables):
        current_tab_line = tab._lineno if tab._lineno is not None else prev_tab_line + 1
        sorted_tables.append((current_tab_line, tab))
        prev_tab_line = current_tab_line
    # print(f"DEBUG: filewriters.py table_sorter {sorted_tables[:]}")
    sorted_result = sorted(sorted_tables, key=lambda x: x[0] in sorted_tables)
    sorted_tables = [z[1] for z in sorted_result]
    return sorted_tables


def FileWriter(context):
    """Creates and returns a ``FileWriter`` object.

    :param context: The type of the returned ``FileWriter`` is determined based
        on ``context.format``. ``context`` is also passed to created writer.
    :type context: :class:`~robot.writer.datafilewriter.WritingContext`
    """
    # if context.format == context.html_format:
    #     return HtmlFileWriter(context)
    if context.format == context.tsv_format:
        return TsvFileWriter(context)
    if context.pipe_separated:
        return PipeSeparatedTxtWriter(context)
    return SpaceSeparatedTxtWriter(context)


class _DataFileWriter(object):

    def __init__(self, formatter, configuration):
        self._formatter = formatter
        self._output = configuration.output
        self.language = configuration.language

    def write(self, datafile):
        tables = [table for table in datafile if table]
        if datafile.has_preamble:
            self._write_preamble(datafile.preamble)
        sorted_tables = table_sorter(tables)
        for table in sorted_tables:
            self._write_table(table, is_last=table is sorted_tables[-1])

    def _write_table(self, table, is_last):
        # print(f"DEBUG: lib.robot.writer _DataFileWriter ENTER _write_table table={table.type}")
        self._write_header(table)
        if table.type == 'comments':
            # print(f"DEBUG: filewriters.py _write_table COMMENTS: {table}")
            if table.is_started():
                self._write_lines(table.section_comments)
                # if len(table.section_comments[-1]) == 0:
            return  # Don't add empty line
        else:
            self._write_rows(self._formatter.format_table(table))
        if not is_last:  # DEBUG: make this configurable
            # print(f"DEBUG: lib.robot.writer _DataFileWritter write_table empty_row table={table.type}")
            try:
                if table.type == 'variable' and len(list(table)[-1].as_list()) == 0:
                    # DEBUG: This is workaround for newline being added ALWAYS to VariableTable
                    #  table.type == 'comments' or
                    return
            except IndexError:
                pass
            self._write_empty_row(table)

    def _write_header(self, table):
        self._write_row(self._formatter.format_header(table))

    def _write_rows(self, rows):
        for row in rows:
            self._write_row(row)

    def _write_empty_row(self, table):
        self._write_row(self._formatter.empty_row_after(table))

    def _write_row(self, row):
        raise NotImplementedError

    def _write_preamble(self, rows):
        for line in rows:
            self._output.write(line)

    def _write_lines(self, rows):
        for line in rows:
            self._output.write(f"{line}\n")


class SpaceSeparatedTxtWriter(_DataFileWriter):

    def __init__(self, configuration):
        formatter = TxtFormatter(column_count=configuration.txt_column_count, language=configuration.language)
        self._separator = ' ' * configuration.txt_separating_spaces
        _DataFileWriter.__init__(self, formatter, configuration)

    def _write_row(self, row):
        line = self._separator.join(row).rstrip() + '\n'
        self._output.write(line)


class PipeSeparatedTxtWriter(_DataFileWriter):
    _separator = ' | '

    def __init__(self, configuration):
        formatter = PipeFormatter(configuration.txt_column_count)
        _DataFileWriter.__init__(self, formatter, configuration)

    def _write_row(self, row):
        row = self._separator.join(row)
        if row:
            row = '| ' + row + ' |'
        self._output.write(row + '\n')


class TsvFileWriter(_DataFileWriter):

    def __init__(self, configuration):
        if not csv:
            raise RuntimeError('No csv module found. '
                               'Writing tab separated format is not possible.')
        formatter = TsvFormatter(configuration.tsv_column_count)
        _DataFileWriter.__init__(self, formatter, configuration)
        self._writer = self._get_writer(configuration)

    @staticmethod
    def _get_writer(configuration):
        # Custom dialect needed as a workaround for
        # http://ironpython.codeplex.com/workitem/33627
        dialect = csv.excel_tab()
        dialect.lineterminator = configuration.line_separator if PY2 else '\n'
        return csv.writer(configuration.output, dialect=dialect)

    def _write_row(self, row):
        if PY2:
            row = [c.encode('UTF-8') for c in row]
        self._writer.writerow(row)


class HtmlFileWriter(_DataFileWriter):

    def __init__(self, configuration):
        formatter = HtmlFormatter(configuration.html_column_count)
        _DataFileWriter.__init__(self, formatter, configuration)
        self._name = configuration.datafile.name
        self._writer = HtmlWriter(configuration.output)

    def write(self, datafile):
        self._writer.content(TEMPLATE_START % {'NAME': self._name}, escape=False)
        _DataFileWriter.write(self, datafile)
        self._writer.content(TEMPLATE_END, escape=False)

    def _write_table(self, table, is_last):
        self._writer.start('table', {'id': table.type.replace(' ', ''),
                                     'border': '1'})
        _DataFileWriter._write_table(self, table, is_last)
        self._writer.end('table')

    def _write_row(self, row):
        self._writer.start('tr')
        for cell in row:
            self._writer.element(cell.tag, cell.content, cell.attributes,
                                 escape=False)
        self._writer.end('tr')
