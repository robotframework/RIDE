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

import atexit
import glob
import io
import os
import sys
import tempfile
import uuid

from .logwindow import LogWindow, message_to_string
from .. import context
from .. import widgets
from ..pluginapi import Plugin
from ..action import ActionInfo
from ..publish.messages import RideLog


class LogPlugin(Plugin):
    """Viewer for internal log messages."""

    def __init__(self, app):
        Plugin.__init__(self, app, default_settings={
            'log_to_console': False,
            'log_to_file': True
        })
        self.title = 'RIDE Log'
        self._log = []
        self._panel = None
        self._path = os.path.join(
            tempfile.gettempdir(), '{}-ride.log'.format(uuid.uuid4()))
        self._outfile = None
        self._remove_old_log_files()
        atexit.register(self._close)

    def _close(self):
        if self._outfile is not None:
            self._outfile.close()

    @staticmethod
    def _remove_old_log_files():
        for fname in glob.glob(
                os.path.join(tempfile.gettempdir(), '*-ride.log')):
            try:
                os.remove(fname)
            except (OSError, IOError) as e:
                sys.stderr.write(f"Removing old *-ride.log files failed with: {repr(e)}\n")

    @property
    def _logfile(self):
        if self._outfile is None:
            self._outfile = io.open(self._path, 'w', encoding='utf8')
        return self._outfile

    def enable(self):
        self._create_menu()
        self.subscribe(self._log_message, RideLog)

    def disable(self):
        self.unsubscribe_all()
        self.unregister_actions()
        if self._panel:
            self._panel.close(self.notebook)

    def _create_menu(self):
        self.unregister_actions()
        self.register_action(ActionInfo(
            'Tools', 'View RIDE Log', self.on_view_log, position=84))

    def _log_message(self, message):
        self._log.append(message)
        if self._panel:
            self._panel.update_log()
        if self.log_to_console:
            print('{}'.format(message_to_string(message)))
        if self.log_to_file:
            self._logfile.write(message_to_string(message))
            self._outfile.flush()
        if message.notify_user:
            font_size = 13 if context.IS_MAC else -1
            widgets.HtmlDialog(message.level, message.message,
                               padding=10, font_size=font_size).Show()

    def on_view_log(self, event):
        _ = event
        if not self._panel:
            self._panel = LogWindow(self.notebook, self.title, self._log)
            self._panel.update_log()
            self.register_shortcut('CtrlCmd-C', lambda e: self._panel.Copy())
        else:
            self.notebook.show_tab(self._panel)
