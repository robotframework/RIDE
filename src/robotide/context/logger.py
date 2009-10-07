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
    trace = debug = info = lambda self, msg: None

    def warn(self, msg=''):
        self.write(msg, 'WARN')

    def error(self, msg=''):
        self.write(msg, 'ERROR')

    def write(self, msg, level):
        self._raise_if_no_ride_warning(msg)
        level = level.upper()
        if level == 'ERROR':
            self._show_message(level, msg, wx.ICON_ERROR)
        elif level == 'WARN':
            self._show_message(level, msg, wx.ICON_WARNING)

    def message(self, msg):
        self.write(msg.message, msg.level)

    def _show_message(self, level, msg, icon):
        if self._is_ignored_warning(msg):
            return
        try:
            wx.MessageBox(msg, level, icon)
        except wx.PyNoAppError:
            sys.stderr.write('%s: %s\n' % (level, msg))

    def _raise_if_no_ride_warning(self, msg):
        res = self.no_ride_regexp.search(msg)
        if res:
            raise NoRideError("Test data file '%s' is not supposed to be "
                              "edited with RIDE." % res.group(1))

    def _is_ignored_warning(self, msg):
        return self.empty_suite_init_file_warn.search(msg)
