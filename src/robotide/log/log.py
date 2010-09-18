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
from robotide.pluginapi import Plugin, ActionInfo
from robotide.publish.messages import RideLogMessage
import wx
from robotide.context.font import Font


class LogPlugin(Plugin):
    """Log for internal log messages.
    """

    def __init__(self, app):
        Plugin.__init__(self, app)
        self._log = []
        self._window = None
        self.subscribe(self._log_message, RideLogMessage)

    def enable(self):
        self._create_menu()

    def _create_menu(self):
        self.unregister_actions()
        self.register_action(ActionInfo('Tools', 'View Log',
                                        self.OnViewLog))

    def _log_message(self, event):
        self._log.append(event.message)
        if self._window:
            self._window.update_log()

    def OnViewLog(self, event):
        if not self._window:
            self._window = _LogWindow(self.notebook, self._log)
            self._window.update_log()
        else:
            self.notebook.show_tab(self._window)


class _LogWindow(wx.ScrolledWindow):

    def __init__(self, notebook, log):
        wx.ScrolledWindow.__init__(self, notebook)
        self._create_ui()
        self._log = log
        self._add_to_notebook(notebook)

    def _create_ui(self):
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self._create_output())
        self.SetSizer(sizer)
        self.SetScrollRate(20, 20)

    def _create_output(self):
        self._output = _OutputDisplay(self)
        return self._output

    def _add_to_notebook(self, notebook):
        notebook.add_tab(self, 'Log', allow_closing=True)
        notebook.show_tab(self)

    def update_log(self):
        self._output.update(self._log)
        self.SetVirtualSize(self._output.Size)

class _OutputDisplay(wx.StaticText):

    def __init__(self, parent):
        wx.StaticText.__init__(self, parent)
        self.SetFont(Font().fixed)

    def update(self, log):
        self.SetLabel(self._decode_log(log))

    def _decode_log(self, log):
        result = ''
        for msg in log:
            result += '%s\n' % msg
        return result

    def clear(self):
        self.SetLabel('')

