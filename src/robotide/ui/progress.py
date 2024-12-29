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

import time

import wx

from .. import context


class ProgressObserver(object):

    def __init__(self, frame, title, message):
        self._progressbar = wx.ProgressDialog(title, message,
                                              maximum=100, parent=frame,
                                              style=wx.PD_ELAPSED_TIME)

    def notify(self):
        self._progressbar.Pulse()

    def finish(self):
        try:
            self._progressbar.Destroy()
        except RuntimeError:
            pass
        if hasattr(context.LOG, 'report_parsing_errors'):
            context.LOG.report_parsing_errors()

    def error(self, msg):
        self.finish()
        if hasattr(context.LOG, 'error'):
            context.LOG.error(msg)


class LoadProgressObserver(ProgressObserver):

    def __init__(self, frame):
        ProgressObserver.__init__(self, frame, 'RIDE', 'Loading the test data')


class RenameProgressObserver(ProgressObserver):

    def __init__(self, frame):
        ProgressObserver.__init__(self, frame, 'RIDE', 'Renaming')
        self._notification_occured = 0

    def notify(self):
        if time.time() - self._notification_occured > 0.1:
            try:
                self._progressbar.Pulse()
            except RuntimeError:
                pass
            self._notification_occured = time.time()
