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
from robotide.lib.robot.utils import JYTHON, Utf8Reader, prepr

NBSP = u'\xa0'


class RobotReader(object):

    def __init__(self, spaces=2):
        self._space_splitter = re.compile("[ \t\xa0]{"+f"{spaces}"+",}|\t+")
        self._pipe_splitter = re.compile(u'[ \t\xa0]+\|(?=[ \t\xa0]+)')
        self._pipe_starts = ('|', '| ', '|\t', u'|\xa0')
        self._pipe_ends = (' |', '\t|', u'\xa0|')

    def read(self, file, populator, path=None):
        path = path or getattr(file, 'name', '<file-like object>')
        # print(f"DEBUG: RobotReader enter read file ({type(file)}) populator {populator} path {path}")
        process = False
        for lineno, line in enumerate(Utf8Reader(file).readlines(), start=1):
            # print(f"DEBUG: reader before row({lineno}) split: line={line}")
            cells = self.split_row(line.rstrip())
            # print(f"DEBUG: reader after row split: cells={cells}\n")
            cells = list(self._check_deprecations(cells, path, lineno))
            if cells and cells[0].strip().startswith('*') and \
                    populator.start_table([c.replace('*', '').strip()
                                           for c in cells]):
                process = True
            elif process:
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
                index = i
                break
            else:
                i += 1
        if index < len(line):
            # print(f"DEBUG: reader sharp_strip line {len(line)} index={index} split={line[:(index-1)]}")
            cells = self._space_splitter.split(line[:(index-1)])
            # print(f"DEBUG: reader sharp_strip cells={cells}")
            row.extend(cells)
            row.append(line[index:])
            # print(f"DEBUG: reader sharp_strip final")
        else:
            # print(f"DEBUG: reader sharp_strip normal split")
            row = self._space_splitter.split(line)
        # print(f"DEBUG: reader sharp_strip returning row={row}")
        return row

    def split_row(self, row):
        if row[:2] in self._pipe_starts:
            row = row[1:-1] if row[-2:] in self._pipe_ends else row[1:]
            return [self._strip_whitespace(cell)
                    for cell in self._pipe_splitter.split(row)]
        return self.sharp_strip(row)
        # print(f"DEBUG: reader split_row before space_splitter: row={row}")
        # return cls._space_splitter.split(row)

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

    def _normalize_whitespace(self, string):
        if string.startswith('#'):
            return string
        return ' '.join(string.split())
