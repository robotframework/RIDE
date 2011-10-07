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


from robot import utils

from logger import LOGGER
from loggerhelper import IsLogged


def DebugFile(path):
    if path == 'NONE':
        LOGGER.info('No debug file')
        return None
    try:
        LOGGER.info('Debug file: %s' % path)
        return _DebugFileWriter(path)
    except:
        LOGGER.error("Opening debug file '%s' failed and writing to debug file "
                     "is disabled. Error: %s" % (path, utils.get_error_message()))
        return None


class _DebugFileWriter:

    _separators = {'SUITE': '=', 'TEST': '-', 'KW': '~'}

    def __init__(self, path):
        self._indent = 0
        self._kw_level = 0
        self._separator_written_last = False
        self._file = open(path, 'wb')
        self._is_logged = IsLogged('DEBUG')

    def start_suite(self, suite):
        self._separator('SUITE')
        self._start('SUITE', suite.longname)
        self._separator('SUITE')

    def end_suite(self, suite):
        self._separator('SUITE')
        self._end('SUITE', suite.longname, suite.elapsedtime)
        self._separator('SUITE')
        if self._indent == 0:
            LOGGER.output_file('Debug', self._file.name)
            self.close()

    def start_test(self, test):
        self._separator('TEST')
        self._start('TEST', test.name)
        self._separator('TEST')

    def end_test(self, test):
        self._separator('TEST')
        self._end('TEST', test.name, test.elapsedtime)
        self._separator('TEST')

    def start_keyword(self, kw):
        if self._kw_level == 0:
            self._separator('KW')
        self._start(self._get_kw_type(kw), kw.name, kw.args)
        self._kw_level += 1

    def end_keyword(self, kw):
        self._end(self._get_kw_type(kw), kw.name, kw.elapsedtime)
        self._kw_level -= 1

    def log_message(self, msg):
        if self._is_logged(msg.level):
            self._write(msg.message)

    def close(self):
        if not self._file.closed:
            self._file.close()

    def _get_kw_type(self, kw):
        if kw.type in ['setup','teardown']:
            return kw.type.upper()
        return 'KW'

    def _start(self, type_, name, args=''):
        args = ' ' + utils.seq2str2(args)
        self._write('+%s START %s: %s%s' % ('-'*self._indent, type_, name, args))
        self._indent += 1

    def _end(self, type_, name, elapsed):
        self._indent -= 1
        self._write('+%s END %s: %s (%s)' % ('-'*self._indent, type_, name, elapsed))

    def _separator(self, type_):
        self._write(self._separators[type_] * 78, True)

    def _write(self, text, separator=False):
        if self._separator_written_last and separator:
            return
        self._file.write(utils.unic(text).encode('UTF-8').rstrip() + '\n')
        self._file.flush()
        self._separator_written_last = separator
