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

import re
import sys
import wx

from robotide.errors import NoRideError


class Logger(object):
    no_ride_regexp = re.compile("'(.*?)'.*no ride", re.IGNORECASE)
    empty_suite_init_file_warn = re.compile("Test suite directory initialization "
                                            "file '.*' contains no test data.")

    def __init__(self):
        self._messages = []

    def report_parsing_errors(self):
        errors = '\n'.join([m[0] for m in self._messages])
        level = 'ERROR' in [m[1] for m in self._messages] and 'ERROR' or 'WARN'
        if errors:
            self._write('Following parsing errors occurred:\n' + errors, level)
        self._messages = []

    def warn(self, msg=''):
        self._write(msg, 'WARN')

    def error(self, msg=''):
        self._write(msg, 'ERROR')

    def message(self, msg):
        message, level = msg.message, msg.level.upper()
        self._raise_if_no_ride_warning(message)
        if self._is_logged(level):
            self._messages.append((message, level))

    def _write(self, msg, level):
        level = level.upper()
        if self._is_logged(level) and not self._is_ignored_warning(msg):
            self._show_message(msg, level)

    def _is_logged(self, level):
        return level.upper() in ['ERROR', 'WARN']

    def _raise_if_no_ride_warning(self, msg):
        res = self.no_ride_regexp.search(msg)
        if res:
            raise NoRideError("Test data file '%s' is not supposed to be "
                              "edited with RIDE." % res.group(1))

    def _is_ignored_warning(self, msg):
        return self.empty_suite_init_file_warn.search(msg)

    def _show_message(self, msg, level):
        try:
            icon = level == 'ERROR' and wx.ICON_ERROR or wx.ICON_WARNING
            wx.MessageBox(msg, level, icon)
        except wx.PyNoAppError:
            sys.stderr.write('%s: %s\n' % (level, msg))
