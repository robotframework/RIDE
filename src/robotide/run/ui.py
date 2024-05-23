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

import builtins
import wx

from .process import Process
from ..widgets import Label, Font

_ = wx.GetTranslation  # To keep linter/code analyser happy
builtins.__dict__['_'] = wx.GetTranslation

FINNISHED = _('finished')
RUN_AGAIN = _('Run Again')
RUNNING = _('running')
STOP = _('Stop')


def get_label(label: str) -> str:
    if label == RUN_AGAIN:
        return 'on_run_again'
    if label == STOP:
        return 'on_stop'
    raise ValueError


class Runner(wx.EvtHandler):

    def __init__(self, config, notebook):
        wx.EvtHandler.__init__(self)
        self.Bind(wx.EVT_TIMER, self.on_timer)
        self.name = config.name
        self._process = None
        self._timer = wx.Timer(self)
        self._config = config
        self._window = self._get_output_window(notebook)

    def _get_output_window(self, notebook):
        return _OutputWindow(notebook, self)

    def run(self):
        self._process = Process(self._config.command)
        # print(f"DEBUG: runanything.py Runner run process object={self._process}"
        #      f"\nCommand: {self._config.command}")
        if self._process is None:
            wx.MessageBox(f"FAILED TO RUN {self._config.command}", style=wx.ICON_ERROR)
            return
        try:
            self._process.start()
            self._timer.Start(500)
        except Exception as err:
            wx.MessageBox(str(err), style=wx.ICON_ERROR)

    def on_timer(self, event=None):
        __ = event
        finished = self._process.is_finished()
        self._window.update_output(self._process.get_output(), finished)
        if finished:
            self._timer.Stop()

    def stop(self):
        try:
            self._process.stop()
        except Exception as err:
            wx.MessageBox(str(err), style=wx.ICON_ERROR)


class _OutputWindow(wx.ScrolledWindow):

    def __init__(self, notebook, runner):
        wx.ScrolledWindow.__init__(self, notebook)
        self._create_ui()
        self._add_to_notebook(notebook, runner.name)
        self._runner = runner

    def _create_ui(self):
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self._create_state_button())
        sizer.Add(self._create_output())
        self.SetSizer(sizer)
        self.SetScrollRate(20, 20)

    def _create_state_button(self):
        self._state_button = _StopAndRunAgainButton(self)
        return self._state_button

    def _create_output(self):
        self._output = _OutputDisplay(self)
        return self._output

    def _add_to_notebook(self, notebook, name):
        notebook.add_tab(self, f"{name} ({RUNNING})", allow_closing=False)
        notebook.show_tab(self)

    def update_output(self, output, finished=False):
        if output:
            self._output.update(output)
            self.SetVirtualSize(self._output.Size)
        if finished:
            self._rename_tab(f"{self._runner.name} ({FINNISHED})")
            self.Parent.allow_closing(self)
            self._state_button.enable_run_again()

    def on_stop(self):
        self.Parent.allow_closing(self)
        self._runner.stop()

    def on_run_again(self):
        self._output.clear()
        self._rename_tab(f"{self._runner.name} ({RUNNING})")
        self.Parent.disallow_closing(self)
        self._state_button.reset()
        self._runner.run()

    def _rename_tab(self, name):
        self.Parent.rename_tab(self, name)


class _OutputDisplay(Label):

    def __init__(self, parent):
        Label.__init__(self, parent)
        self.SetFont(Font().fixed)

    def update(self, addition):
        try:
            self.SetLabel(self.LabelText + addition.decode('UTF-8', 'ignore'))
        except AttributeError:
            self.SetLabel(self.LabelText + "ERROR")
            getattr(self.Parent, 'on_stop')()

    def clear(self):
        self.SetLabel('')


class _StopAndRunAgainButton(wx.Button):

    def __init__(self, parent):
        wx.Button.__init__(self, parent, label=STOP)
        self.Bind(wx.EVT_BUTTON, self.on_click, self)

    def on_click(self, event):
        __ = event
        self.Enable(False)
        name = get_label(self.LabelText)
        getattr(self.Parent, name)()

    def enable_run_again(self):
        self.Enable()
        self.SetLabel(RUN_AGAIN)

    def reset(self):
        self.Enable()
        self.SetLabel(STOP)
