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

import os

from template import Template
from writer import FileWriter


class Serializer(object):

    def __init__(self, output=None, pipe_separator=False):
        self._output = output
        self._pipe_separator = pipe_separator

    def serialize(self, controller):
        template = self._create_template(controller)
        output = self._get_output(controller)
        writer = FileWriter(controller.source, output, name=controller.name,
                            template=template, pipe_separator=self._pipe_separator)
        writer_serializer = _WriterSerializer(writer)
        writer_serializer.serialize(controller.data)
        self._close_output(writer)

    def _create_template(self, controller):
        ext = os.path.splitext(controller.source)[1].lower()
        return Template(controller.source, controller.name) if \
            ext in ['.html', '.xhtml', '.htm'] else None

    def _get_output(self, controller):
        if self._output:
            return self._output
        return open(controller.source, 'wb')

    def _close_output(self, writer):
        writer.close(close_output=self._output is None)


class _WriterSerializer(object):

    def __init__(self, writer):
        self._writer = writer
        self.table_handlers = {'setting': self._setting_table_handler,
                               'variable': self._variable_table_handler,
                               'keyword': self._keyword_table_handler,
                               'testcase': self._testcase_table_handler}

    def serialize(self, datafile):
        for table in datafile:
            if table:
                self.table_handlers[table.type](table)

    def _setting_table_handler(self, table):
        self._writer.start_settings()
        self._write_elements(table)
        self._writer.end_settings()

    def _write_elements(self, elements):
        for element in elements:
            if element.is_for_loop():
                self._handle_for_loop(element)
            elif element.is_set():
                self._writer.element(element)

    def _handle_for_loop(self, loop):
        self._writer.start_for_loop(loop)
        self._write_elements(loop)
        self._writer.end_for_loop()

    def _variable_table_handler(self, table):
        self._writer.start_variables()
        self._write_elements(table)
        self._writer.end_variables()

    def _keyword_table_handler(self, table):
        self._writer.start_keywords()
        for kw in table:
            self._handle_keyword(kw)
        self._writer.end_keywords()

    def _handle_keyword(self, kw):
        self._writer.start_keyword(kw)
        self._write_elements(kw)
        self._writer.end_keyword()

    def _testcase_table_handler(self, table):
        self._writer.start_testcases()
        for tc in table:
            self._handle_testcase(tc)
        self._writer.end_testcases()

    def _handle_testcase(self, tc):
        self._writer.start_testcase(tc)
        self._write_elements(tc)
        self._writer.end_testcase()
