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

from robotide.lib.robot.output import LOGGER
from robotide.lib.robot.utils import Utf8Reader, prepr

NBSP = u'\xa0'


class RobotReader(object):

    def __init__(self, spaces=2):
        self._spaces = spaces
        self._space_splitter = re.compile(r"[ \t\xa0]{2}|\t+")
        self._pipe_splitter = re.compile(r"[ \t\xa0]+\|(?=[ \t\xa0]+)")
        self._pipe_starts = ('|', '| ', '|\t', u'|\xa0')
        self._pipe_ends = (' |', '\t|', u'\xa0|')
        self._separator_check = False
        self._cell_section = False

    def read(self, file, populator, path=None):
        path = path or getattr(file, 'name', '<file-like object>')
        _ = path
        process = table_start = preamble = False
        # print(f"DEBUG: RFLib RobotReader start Reading file")
        for lineno, line in enumerate(Utf8Reader(file).readlines(), start=1):
            if not self._separator_check:
                self.check_separator(line.rstrip())
            cells = self.split_row(line.rstrip())
            if cells and cells[0].strip().startswith('*'):  # For the cases of *** Comments ***
                if cells[0].replace('*', '').strip().lower() in ('comment', 'comments'):
                    # print(f"DEBUG: robotreader.read detection of comments cells={cells}")
                    process = True
            if cells and cells[0].strip().startswith('*') and \
                    populator.start_table([c.replace('*', '').strip() for c in cells]):
                process = table_start = True
                preamble = False  # DEBUG removed condition  "and not comments" comments =
            elif not table_start:
                # print(f"DEBUG: RFLib RobotReader Enter Preamble block, lineno={lineno} cells={cells}")
                if not preamble:
                    preamble = True
                populator.add_preamble(line)
            elif process and not preamble:
                populator.add(cells)
        return populator.eof()

    def sharp_strip(self, line):
        row = self._space_splitter.split(line)
        # print(f"DEBUG: RFLib RobotReader sharp_strip after cells split row={row[:]}")
        return row

    def split_row(self, row):
        if row[:2] in self._pipe_starts:
            row = row[1:-1] if row[-2:] in self._pipe_ends else row[1:]
            return [self._strip_whitespace(cell)
                    for cell in self._pipe_splitter.split(row)]
        return self.sharp_strip(row)

    def _check_deprecations(self, cells, path, line_number):
        for original in cells:
            normalized = self._normalize_whitespace(original)
            if normalized != original:
                if len(normalized) != len(original):
                    msg = 'Collapsing consecutive whitespace'
                else:
                    msg = 'Converting whitespace characters to ASCII spaces'
                LOGGER.warn("%s during parsing is deprecated. Fix %s in file "
                            "'%s' on line %d."
                            % (msg, prepr(original), path, line_number))
            yield normalized

    @classmethod
    def _strip_whitespace(cls, string):
        return string.strip()

    @staticmethod
    def _normalize_whitespace(string):
        if string.startswith('#'):
            return string
        return ' '.join(string.split())

    def check_separator(self, line):
        if line.startswith('*') and not self._cell_section:
            row = line.strip('*').strip().lower()
            if row in ['keyword', 'keywords', 'test case', 'test cases', 'task', 'tasks', 'variable', 'variables']:
                self._cell_section = True
        if not line.startswith('*') and not line.startswith('#'):
            if not self._separator_check and line[:2] in self._pipe_starts:
                self._separator_check = True
                # print(f"DEBUG: RFLib RobotReader check_separator PIPE separator")
                return
            if not self._cell_section:
                return
            idx = 0
            for idx in range(0, len(line)):
                if line[idx] != ' ':
                    break
            if 2 <= idx <= 10:  # This max limit is reasonable
                self._spaces = idx
                self._space_splitter = re.compile(r"[ \t\xa0]{" + f"{self._spaces}" + "}|\t+")
                self._separator_check = True
                # print(f"DEBUG: RFLib RobotReader check_separator changed spaces={self._spaces}")
