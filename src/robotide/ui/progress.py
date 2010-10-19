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

import wx

from robotide import context


class LoadProgressObserver(object):

    def __init__(self, frame):
        self._progressbar = wx.ProgressDialog('RIDE', 'Loading the test data',
                                              maximum=100, parent=frame,
                                              style=wx.PD_ELAPSED_TIME)

    def notify(self):
        self._progressbar.Pulse()

    def finish(self):
        self._progressbar.Destroy()
        context.LOG.report_parsing_errors()

    def error(self, msg):
        self.finish()
        context.LOG.error(msg)
