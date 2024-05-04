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

from robotide.lib.compat.parsing import language
from robotide.lib.robot.output import LOGGER
from robotide.lib.robot.utils import Utf8Reader, prepr

NBSP = u'\xa0'


class RobotReader(object):

    def __init__(self, spaces=2, lang=None):
        self._spaces = spaces
        self._space_splitter = re.compile(r"[ \t\xa0]{2}|\t+")
        self._pipe_splitter = re.compile(r"[ \t\xa0]+\|(?=[ \t\xa0]+)")
        self._pipe_starts = ('|', '| ', '|\t', u'|\xa0')
        self._pipe_ends = (' |', '\t|', u'\xa0|')
        self._separator_check = False
        self._cell_section = False
        self.language = lang

    def read(self, file, populator, path=None):
        path = path or getattr(file, 'name', '<file-like object>')
        _ = path
        # print(f"DEBUG: robotreader.read ENTER path={path}")
        process = table_start = preamble = False
        # print(f"DEBUG: RFLib RobotReader start Reading file language={self.language}")
        for lineno, line in enumerate(Utf8Reader(file).readlines(), start=1):
            if not self._separator_check:
                self.check_separator(line.rstrip())
            cells = self.split_row(line.rstrip())
            if cells and cells[0].strip().startswith('*') and \
                    populator.start_table([c.replace('*', '').strip() for c in cells], lineno=lineno,
                                          llang=self.language):
                process = table_start = True
                preamble = False  # DEBUG removed condition  "and not comments" comments =
                # print(f"DEBUG: RobotReader After table_start head={cells[0].replace('*', '').strip()}")
            elif not table_start:
                # print(f"DEBUG: RFLib RobotReader Enter Preamble block, lineno={lineno} cells={cells}")
                if not preamble:
                    preamble = True
                populator.add_preamble(line)
            elif process and not preamble:
                # print(f"DEBUG: RFLib RobotReader before add cells={cells} populator is={populator}")
                populator.add(cells)
                # print(f"DEBUG: RFLib RobotReader after add cells={cells}")
        return populator.eof()

    def sharp_strip(self, line):
        if self._separator_check:
            row = self._space_splitter.split(line)
            # print(f"DEBUG: RFLib RobotReader sharp_strip after cells split spaces={self._spaces} row={row[:]}")
            return [c.strip() for c in row]
        row = []
        start = end = no_spc = spc = 0
        for idx in range(len(line)):
            if line[idx] != ' ':
                no_spc += 1
                end = idx
                if spc > max(2, self._spaces - 1) or idx == len(line) - 1:
                    if idx == len(line) - 1:
                        end = None
                    segmt = line[start:end].strip()   # Spaces cell
                    # print(f"DEBUG: robotreader.py sharp_strip in non_spc {idx=} {segmt} {end=}")
                    row.append(segmt)
                    start = idx
                spc = 0
            else:
                spc += 1
                end = idx
                if (no_spc > 0 and spc >= max(2, self._spaces - 1)) or idx == len(line) - 1:
                    if idx == len(line) - 1:
                        end = None
                    segmt = line[start:end].strip()  # No spaces cell
                    # print(f"DEBUG: robotreader.py sharp_strip in spc {idx=} {segmt} {end=}")
                    row.append(segmt)
                    start = idx
                no_spc = 0
        spc_row = []
        for r in row:
            spc_row.extend(r.split(max(2, self._spaces) * ' '))
            # spc_row.extend(self._space_splitter.split(r))
        # Remove empty cells after first identation or content
        content = False
        for idx, r in enumerate(spc_row):
            if r != '':
                content = True
            if r == '' and content:
                spc_row.pop(idx)
        # print(f"DEBUG: robotreader.py sharp_strip splitted line={spc_row[:]}[{len(''.join(spc_row))}]\n"
        #       f"original line={line}[{len(line)}]")
        return spc_row

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
        # print(f"DEBUG: robotreader.check_separator ENTER line={line}")
        if line.startswith('*'):  # DEBUG: we want to recheck for new sections, was: and not self._cell_section:
            row = line.strip('*').strip().lower()
            # print(f"DEBUG: robotreader.check_separator SECTION CHECK row={row} lang={self.language}")
            if row in language.get_headers_for(self.language, ['keyword', 'keywords', 'test case',
                                                               'test cases', 'task', 'tasks', 'variable', 'variables']):
                # print(f"DEBUG: robotreader.check_separator detection of cell section row={row}")
                self._cell_section = True
                self._separator_check = False
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
