#  Copyright 2008-2015 Nokia Solutions and Networks
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
import os
import tempfile
import uuid
import atexit
import glob
import sys

from robotide.pluginapi import Plugin, ActionInfo, RideLog
from robotide import widgets
from robotide import context


def _message_to_string(msg):
    return '%s [%s]: %s\n\n' % (msg.timestamp, msg.level, msg.message)


class LogPlugin(Plugin):
    """Viewer for internal log messages."""

    def __init__(self, app):
        Plugin.__init__(self, app, default_settings={
            'log_to_console': False,
            'log_to_file': True
        })
        self._log = []
        self._window = None
        self._path = os.path.join(
            tempfile.gettempdir(), '{}-ride.log'.format(uuid.uuid4()))
        self._outfile = None
        self._remove_old_log_files()
        atexit.register(self._close)

    def _close(self):
        if self._outfile is not None:
            self._outfile.flush()
            self._outfile.close()

    def _remove_old_log_files(self):
        for fname in glob.glob(
                os.path.join(tempfile.gettempdir(), '*-ride.log')):
            try:
                os.remove(fname)
            except OSError or IOError as e:
                sys.stderr.write("{}".format(e))

    @property
    def _logfile(self):
        if self._outfile is None:
            self._outfile = open(self._path, 'w')
        return self._outfile

    def enable(self):
        self._create_menu()
        self.subscribe(self._log_message, RideLog)

    def disable(self):
        self.unsubscribe_all()
        self.unregister_actions()
        if self._window:
            self._window.close(self.notebook)

    def _create_menu(self):
        self.unregister_actions()
        self.register_action(ActionInfo(
            'Tools', 'View RIDE Log', self.OnViewLog, position=84))

    def _log_message(self, log_event):
        self._log.append(log_event)
        if self._window:
            self._window.update_log()
        if self.log_to_console:
            print _message_to_string(log_event)
        if self.log_to_file:
            self._logfile.write(_message_to_string(log_event))
        if log_event.notify_user:
            font_size = 13 if context.IS_MAC else -1
            widgets.HtmlDialog(log_event.level, log_event.message,
                               padding=10, font_size=font_size).Show()

    def OnViewLog(self, event):
        if not self._window:
            self._window = _LogWindow(self.notebook, self._log)
            self._window.update_log()
            self.register_shortcut('CtrlCmd-C', lambda e: self._window.Copy())
            self.register_shortcut(
                'CtrlCmd-A', lambda e: self._window.SelectAll())
        else:
            self.notebook.show_tab(self._window)


class _LogWindow(wx.TextCtrl):

    def __init__(self, notebook, log):
        wx.TextCtrl.__init__(
            self, notebook, style=wx.TE_READONLY | wx.TE_MULTILINE)
        self._log = log
        self._create_ui()
        self._add_to_notebook(notebook)
        self.SetFont(widgets.Font().fixed_log)

    def _create_ui(self):
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self)
        self.SetSizer(sizer)

    def _add_to_notebook(self, notebook):
        notebook.add_tab(self, 'Log', allow_closing=True)
        notebook.show_tab(self)

    def close(self, notebook):
        notebook.delete_tab(self)

    def update_log(self):
        self.SetValue(self._decode_log(self._log))

    def _decode_log(self, log):
        result = ''
        for msg in log:
            result += _message_to_string(msg)
        return result
