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
        # self._space_splitter = re.compile(r"[ \t\xa0]{"+f"{self._spaces}"+"}|\t+")  # Only change when is cell_section
        self._space_splitter = re.compile(r"[ \t\xa0]{2}|\t+")
        self._pipe_splitter = re.compile(r"[ \t\xa0]+\|(?=[ \t\xa0]+)")
        self._pipe_starts = ('|', '| ', '|\t', u'|\xa0')
        self._pipe_ends = (' |', '\t|', u'\xa0|')
        self._separator_check = False
        self._cell_section = False
        # print(f"DEBUG: RFLib RobotReader init spaces={self._spaces}")

    def read(self, file, populator, path=None):
        path = path or getattr(file, 'name', '<file-like object>')
        _ = path
        process = table_start = preamble = comments = False
        # print(f"DEBUG: RFLib RobotReader start Reading file")
        for lineno, line in enumerate(Utf8Reader(file).readlines(), start=1):
            if not self._separator_check:
                self.check_separator(line.rstrip())
            cells = self.split_row(line.rstrip())
            # DEBUG cells = list(self._check_deprecations(cells, path, lineno))
            # DEBUG Not parsing # before any table
            if line.lstrip().startswith('#'):
                if cells[0] == '':  # There is an initial empty cell, when #
                    cells.pop(0)
                # populator.add(cells)
                # continue
            if cells and cells[0].strip().startswith('*'):  # For the cases of *** Comments ***
                if cells[0].replace('*', '').strip().lower() in ('comment', 'comments'):
                    # print(f"DEBUG: robotreader.read detection of comments cells={cells}")
                    process = True
                    comments = True
                    # if not preamble:
                    #     cells.insert(0, '')
                else:
                    # if comments:
                    #    cells.insert(0, '')  # Last comments block
                    comments = False
                # print(f"DEBUG: RFLib RobotReader *** section lineno={lineno} cells={cells}")
            elif cells and cells == ['']:
                comments = False
            if cells and cells[0].strip().startswith('*') and not comments and \
                    populator.start_table([c.replace('*', '').strip() for c in cells]):
                process = table_start = True
                preamble = comments = False
            elif not table_start:
                # print(f"DEBUG: RFLib RobotReader Enter Preamble block, lineno={lineno} cells={cells}")
                if not preamble:
                    preamble = True
                populator.add_preamble(line)
            elif process and not preamble:
                # We modify, insert cell, to avoid being a new test case, keyword...
                # if comments:  # and cells[0] != '':
                #    cells.insert(0, '')
                #    # print(f"DEBUG: robotreader.read in comments cells={cells}")
                # print(f"DEBUG: robotreader.read original line={line}\nparser={cells}")
                populator.add(cells)
        return populator.eof()

    def sharp_strip(self, line):
        row = []
        i = 0
        start_d_quote = end_d_quote = False
        start_s_quote = end_s_quote = False
        index = len(line)
        while i < len(line):
            if line[i] == '"':
                if end_d_quote:
                    start_d_quote = True
                    end_d_quote = False
                elif start_d_quote:
                    end_d_quote = True
                else:
                    start_d_quote = True
            if line[i] == "'":
                if end_s_quote:
                    start_s_quote = True
                    end_s_quote = False
                elif start_s_quote:
                    end_s_quote = True
                else:
                    start_s_quote = True
            if line[i] == '#' and not start_d_quote and not start_s_quote:
                if i == 0:
                    index = 0
                    break
                try:
                    if i > 0 and line[i-1] != '\\' and (line[i+1] == ' ' or line[i+1] == '#'):
                        index = i
                        # print(f"DEBUG: RFLib RobotReader sharp_strip BREAK at # index={index}")
                        break
                except IndexError:
                    i += 1
                    continue
            i += 1
        if index < len(line):
            cells = self._space_splitter.split(line[:index])
            row.extend(cells)
            row.append(line[index:])
        else:
            row = self._space_splitter.split(line)
        # print(f"DEBUG: RFLib RobotReader sharp_strip after cells split index={index} row={row[:]}")
        # Remove empty cells after first non-empty
        first_non_empty = -1
        if row:
            for i, v in enumerate(row):
                if v != '':
                    first_non_empty = i
                    break
            # print(f"DEBUG: RFLib RobotReader sharp_strip row first_non_empty={first_non_empty}")
            if first_non_empty != -1:
                for i in range(len(row)-1, first_non_empty, -1):
                    if row[i] == '':
                        # print(f"DEBUG: RFLib RobotReader sharp_strip popping ow i ={i} row[i]={row[i]}")
                        row.pop(i)
                # Remove initial empty cell
                if len(row) > 1 and first_non_empty > 1 and row[0] == '' and row[1] != '':  # don't cancel indentation
                    # print(f"DEBUG: RFLib RobotReader sharp_strip removing initial empty cell
                    # first_non_empty={first_non_empty}")
                    row.pop(0)
        # print(f"DEBUG: RFLib RobotReader sharp_strip returning row={row[:]}")
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
        """
        if line.startswith('*') and not self._cell_section:
            row = line.strip('*').strip(' ')
            if row in ['Keyword', 'Keywords', 'Test Case', 'Test Cases', 'Task', 'Tasks', 'Variable', 'Variables']:
                self._cell_section = True
                # self._space_splitter = re.compile(r"[ \t\xa0]{" + f"{self._spaces}" + "}|\t+")
        """
        if not line.startswith('*') and not line.startswith('#'):
            if not self._separator_check and line[:2] in self._pipe_starts:
                self._separator_check = True
                # print(f"DEBUG: RFLib RobotReader check_separator PIPE separator")
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
        return
