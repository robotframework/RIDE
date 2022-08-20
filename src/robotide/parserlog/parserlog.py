#  Copyright 2019-     Robot Framework Foundation
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

import wx
from wx import Colour

from .. import context
from .. import widgets
from ..pluginapi import Plugin
from ..action import ActionInfo
from ..publish.messages import RideParserLogMessage
from ..widgets import RIDEDialog

def _message_to_string(msg):
    return '%s [%s]: %s\n\n' % (msg.timestamp, msg.level, msg.message.replace('\n\t', ''))


class ParserLogPlugin(Plugin):
    """Viewer for internal log messages."""

    def __init__(self, app):
        Plugin.__init__(self, app, default_settings={
            'log_to_console': False,
            'log_to_file': True
        })
        self._log = []
        self._panel = None
        self._path = os.path.join(
            tempfile.gettempdir(), '{}-ride_parser.log'.format(uuid.uuid4()))
        self._outfile = None
        self._remove_old_log_files()
        atexit.register(self._close)

    def _close(self):
        if self._outfile is not None:
            self._outfile.close()

    def _remove_old_log_files(self):
        for fname in glob.glob(
                os.path.join(tempfile.gettempdir(), '*-ride_parser.log')):
            try:
                os.remove(fname)
            except OSError or IOError or PermissionError as e:
                sys.stderr.write(f"Removing old *-ride_parser.log files failed with: {repr(e)}\n")
            finally:
                pass

    @property
    def _logfile(self):
        if self._outfile is None:
            self._outfile = io.open(self._path, 'w', encoding='utf8')
        return self._outfile

    def enable(self):
        self._create_menu()
        self.subscribe(self._log_message, RideParserLogMessage)

    def disable(self):
        self.unsubscribe_all()
        self.unregister_actions()
        if self._panel:
            self._panel.close(self.notebook)

    def _create_menu(self):
        self.unregister_actions()
        self.register_action(ActionInfo(
            'Tools', 'View Parser Log', self.OnViewLog, position=83))

    def _log_message(self, message):
        self._log.append(message)
        if self._panel:
            self._panel.update_log()
        if self.log_to_console:
            print("".format(_message_to_string(message)))  # >> sys.stdout, _message_to_string(message)
        if self.log_to_file:
            self._logfile.write(_message_to_string(message))
            self._outfile.flush()
        if message.notify_user:
            font_size = 13 if context.IS_MAC else -1
            widgets.HtmlDialog(message.level, message.message,
                               padding=10, font_size=font_size).Show()
        self.OnViewLog(message, show_tab=False)

    def OnViewLog(self, event, show_tab=True):
        if not self._panel:
            self._panel = _LogWindow(self.notebook, self._log)
            self.notebook.SetPageTextColour(self.notebook.GetPageCount()-1, wx.Colour(255, 165, 0))
            self._panel.update_log()
            self.register_shortcut('CtrlCmd-C', lambda e: self._panel.Copy())
        if show_tab:
            self.notebook.show_tab(self._panel)


class _LogWindow(wx.Panel):

    def __init__(self, notebook, log):
        wx.Panel.__init__(self, notebook)
        self.dlg = RIDEDialog()
        self._output = wx.TextCtrl(self, style=wx.TE_READONLY | wx.TE_MULTILINE | wx.TE_NOHIDESEL)
        self._output.SetBackgroundColour(Colour(self.dlg.color_background))
        self._output.SetForegroundColour(Colour(self.dlg.color_foreground))
        self._output.Bind(wx.EVT_KEY_DOWN, self.OnKeyDown)
        self._log = log
        self._notebook = notebook
        self._add_to_notebook(notebook)
        self.SetFont(widgets.Font().fixed_log)
        self.Bind(wx.EVT_SIZE, self.OnSize)

    def _add_to_notebook(self, notebook):
        notebook.add_tab(self, 'Parser Log', allow_closing=True)
        self._output.SetSize(self.Size)

    def close(self, notebook):
        notebook.delete_tab(self)

    def _create_ui(self):
        self.SetSizer(widgets.VerticalSizer())
        self.Sizer.add_expanding(self._output)

    def update_log(self):
        self._output.SetValue(self._decode_log(self._log))

    def _decode_log(self, log):
        result = ''
        for msg in log:
            result += _message_to_string(msg)
        return result

    def OnSize(self, evt):
        self._output.SetSize(self.Size)

    def OnKeyDown(self, event):
        keycode = event.GetKeyCode()

        if event.ControlDown() and keycode == ord('A'):
            self.SelectAll()
        else:
            event.Skip()

    def Copy(self):
        pass

    def SelectAll(self):
        self._output.SetSelection(-1, -1)
